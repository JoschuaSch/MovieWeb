from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from datamanager.json_data_manager import JSONDataManager, UserNotFoundError, MovieNotFoundError, DuplicateMovieError
import uuid
from werkzeug.exceptions import BadRequest, abort
import omdb_api
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import json
from werkzeug.utils import secure_filename
import os
from urllib.parse import unquote

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
data_manager = JSONDataManager('data.json')
app.config['UPLOAD_FOLDER'] = 'C:/Users/schro/MovieWeb/static/User_picked_profile_pictures'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.route('/')
def home():
    """Render the home page."""
    return render_template('home.html')


@app.route('/users/<user_id>/movies')
@login_required
def user_movies(user_id):
    """Render the page showing movies of a specific user."""
    search = request.args.get('search')
    try:
        if search:
            movies = data_manager.get_user_movies(user_id, search)
        else:
            movies = data_manager.get_user_movies(user_id)
        return render_template('user_movies.html', movies=movies, user_id=user_id, current_user_id=current_user.id)
    except UserNotFoundError:
        return f"User with ID {user_id} not found."


@app.route('/users', methods=['GET', 'POST'])
def list_users():
    """Render the page showing all users."""
    if request.method == 'POST':
        search = request.form.get('search')
        if search:
            users = data_manager.get_users_by_name(search)
        else:
            users = data_manager.get_all_users()
    else:
        users = data_manager.get_all_users()
    return render_template('users.html', users=users)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """Add a new user to the system."""
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        if not name or len(name) > 100:
            raise BadRequest('Invalid user name.')
        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        data_manager.add_user(user_id, name, hashed_password)
        return redirect(url_for('list_users'))
    return render_template('add_user.html')


@app.route('/add_movie', methods=['GET', 'POST'])
@login_required
def add_movie():
    """Add a movie to a user's movie list."""
    if request.method == 'POST':
        movie_name = request.form.get('movie_name')
        if not movie_name:
            flash('No movie name provided. Please check and try again.')
            return redirect(url_for('add_movie'))
        else:
            return redirect(url_for('confirm_movie', user_id=current_user.id, movie_name=movie_name))
    else:
        users = data_manager.get_all_users()
        return render_template('add_movie.html', users=users)


@app.route('/confirm_movie/<user_id>/<movie_name>', methods=['GET', 'POST'])
def confirm_movie(user_id, movie_name):
    """Confirm the movie details before adding it to a user's movie list."""
    if request.method == 'GET':
        movie_data = omdb_api.fetch_movie_details(movie_name)
        if movie_data is None:
            flash('Movie not found. Please check the title and try again.')
            return redirect(url_for('add_movie'))
        else:
            return render_template('confirm_movie.html', user_id=user_id, movie=movie_data)
    else:
        personal_rating = request.form.get('rating')
        watched = 'watched' in request.form
        movie_data = omdb_api.fetch_movie_details(movie_name)
        if movie_data is None:
            flash('Movie not found. Please check the title and try again.')
            return redirect(url_for('add_movie'))
        movie_data['personal_rating'] = personal_rating
        movie_data['watched'] = watched
        try:
            data_manager.add_movie(user_id, movie_data)
            flash('Movie added successfully. Do you want to add more or go to your movie list?')
            return render_template('post_add_movie.html', user_id=user_id)
        except DuplicateMovieError:
            flash('This movie is already in your list.')
            return redirect(url_for('confirm_movie', user_id=user_id, movie_name=movie_name))


@app.route('/users/<user_id>/movies/update/<movie_id>', methods=['GET', 'POST'])
@login_required
def update_movie(user_id, movie_id):
    if current_user.id != user_id:
        abort(403)
    try:
        movie = data_manager.find_movie_by_id(user_id, movie_id)
    except (UserNotFoundError, MovieNotFoundError) as e:
        return render_template('error.html', message=str(e)), 404
    if request.method == 'POST':
        movie_name = request.form.get('name')
        movie_director = request.form.get('director')
        year = request.form.get('year')
        rating = request.form.get('rating')
        watched = 'watched' in request.form
        review = request.form.get('review')
        movie_details = {}
        if movie_name:
            movie_details["Title"] = movie_name
        if movie_director:
            movie_details["Director"] = movie_director
        if year:
            movie_details["Year"] = int(year)
        if rating:
            movie_details["personal_rating"] = float(rating)
        movie_details["watched"] = watched
        if review:
            movie_details["review"] = review
        try:
            data_manager.update_movie(user_id, movie_id, movie_details)
            if watched:
                return redirect(url_for('user_watchlist', user_id=user_id))
            else:
                return redirect(url_for('user_movies', user_id=user_id))
        except MovieNotFoundError as e:
            return render_template('error.html', message=str(e)), 404
    else:
        return render_template('update_movie.html', user_id=user_id, movie_id=movie_id, movie=movie)


@app.route('/users/<user_id>/delete_movie/<movie_id>', methods=['POST'])
@login_required
def delete_movie(user_id, movie_id):
    """Delete a movie from a user's movie list."""
    if current_user.id != user_id:
        abort(403)
    try:
        data_manager.delete_movie(user_id, movie_id)
        flash('Movie deleted successfully.')
        return redirect(url_for('user_movies', user_id=user_id))
    except ValueError as e:
        return render_template('error.html', message=str(e)), 400


@app.errorhandler(404)
def page_not_found():
    """Render the 404 page."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error():
    """Render the 500 page."""
    return render_template('500.html'), 500


class User(UserMixin):
    def __init__(self, user_id, name):
        self.id = user_id
        self.name = name

    @classmethod
    def get(cls, user_id):
        user_data = data_manager.find_user_by_id(user_id)
        if not user_data:
            return None
        return User(user_id, user_data['name'])


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user."""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_id = user_id.capitalize()
        existing_user_data = data_manager.find_user_by_id(user_id)
        if existing_user_data:
            flash('This username is already taken. Please choose a different one.')
            return redirect(url_for('register'))
        password = request.form.get('password')
        password_verify = request.form.get('password_verify')
        if password != password_verify:
            flash('Passwords do not match. Please try again.')
            return redirect(url_for('register'))
        age = request.form.get('age')
        sex = request.form.get('sex')
        words_to_live_by = request.form.get('words_to_live_by')
        favorite_movie = request.form.get('favorite_movie')
        favorite_quote = request.form.get('favorite_quote')
        profile_picture = None
        hashed_password = generate_password_hash(password)
        data_manager.add_user(user_id, user_id, hashed_password, age, favorite_movie, favorite_quote,
                              words_to_live_by, sex, profile_picture)
        flash('Registered successfully. Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in a user."""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user_id = user_id[0].upper() + user_id[1:].lower()
        password = request.form.get('password')
        user_data = data_manager.find_user_by_id(user_id)
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_id, user_data['name'])
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('home'))


@app.route('/top100')
def top_100_movies():
    """Render the page showing the top 100 most watched movies."""
    movie_counts = data_manager.get_most_watched_movies()
    return render_template('top100.html', movie_counts=movie_counts, current_user=current_user)


@app.route('/random-movie', methods=['GET'])
def random_movie():
    """Render the page showing a random movie from the data."""
    with open('data.json', 'r') as f:
        data = json.load(f)

    movie_ids = []
    for user in data.values():
        for movie in user['movies'].values():
            movie_ids.append(movie)
    randomized_movie = random.choice(movie_ids)
    return render_template('random.html', movie=randomized_movie)


@app.route('/users/<user_id>/profile')
@login_required
def user_profile(user_id):
    """Render the profile page of a specific user."""
    try:
        user_data = data_manager.find_user_by_id(user_id)
        if user_data['profile_picture'] is not None:
            profile_picture_path = unquote(user_data['profile_picture'])
            profile_picture = url_for('uploaded_file', filename=profile_picture_path)
        else:
            profile_picture = None
        return render_template('user_profile.html', user=user_data, profile_picture=profile_picture)
    except UserNotFoundError:
        return f"User with ID {user_id} not found."


@app.route('/users/<user_id>/movies/<movie_id>/like', methods=['POST'])
@login_required
def like_review(user_id, movie_id):
    """Like a review for a movie in a user's movie list."""
    try:
        liker_id = current_user.id
        data_manager.like_review(user_id, movie_id, liker_id)
        next_url = request.referrer
        return redirect(next_url)
    except ValueError as e:
        return render_template('error.html', message=str(e)), 400


@app.route('/users/<user_id>/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile(user_id):
    """Update the profile details of a user."""
    if current_user.id != user_id:
        abort(403)
    try:
        user = data_manager.find_user_by_id(user_id)
    except UserNotFoundError:
        return render_template('error.html', message="User not found"), 404
    if request.method == 'POST':
        age = request.form.get('age')
        sex = request.form.get('sex')
        words_to_live_by = request.form.get('words_to_live_by')
        favorite_movie = request.form.get('favorite_movie')
        favorite_quote = request.form.get('favorite_quote')
        profile_picture = request.files.get('profile_picture')
        user_details = {
            "age": age,
            "sex": sex,
            "words_to_live_by": words_to_live_by,
            "favorite_movie": favorite_movie,
            "favorite_quote": favorite_quote,
        }
        if profile_picture:
            filename = secure_filename(user_id + '_' + profile_picture.filename)
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user_details["profile_picture"] = filename
        data_manager.update_user(user_id, user_details)
        return redirect(url_for('user_profile', user_id=user_id))
    else:
        return render_template('update_profile.html', user=user)


@app.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_account(user_id):
    """Delete a user account."""
    if current_user.id != user_id:
        abort(403)
    try:
        data_manager.delete_user(user_id)
        logout_user()
        flash('Your account has been deleted.')
        return redirect(url_for('home'))
    except UserNotFoundError:
        return render_template('error.html', message="User not found"), 404


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files from the UPLOAD_FOLDER directory."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/reviews', methods=['GET'])
def movie_reviews():
    """Render the page showing movie reviews, sorted by likes or date."""
    sort_by = request.args.get('sort_by', 'newest')
    if sort_by == 'liked':
        reviews = data_manager.get_reviews_sorted_by_likes()
    else:
        reviews = data_manager.get_reviews_sorted_by_date()
    return render_template('movie_reviews.html', reviews=reviews, sort_by=sort_by)


@app.route('/users/<user_id>/watchlist')
@login_required
def user_watchlist(user_id):
    """Render the watchlist page of a specific user."""
    try:
        watchlist_movies = data_manager.get_user_watchlist(user_id)
        return render_template('user_watchlist.html', movies=watchlist_movies, user_id=user_id,
                               current_user_id=current_user.id)
    except UserNotFoundError:
        return f"User with ID {user_id} not found."


@app.route('/users/<user_id>/movies/add_to_watchlist', methods=['POST'])
@login_required
def add_to_watchlist(user_id):
    """Add a movie to a user's watchlist."""
    if current_user.id != user_id:
        abort(403)
    movie_name = request.form.get('movie_name')
    if not movie_name:
        flash('No movie name provided. Please check and try again.', 'error')
    try:
        movie_data = omdb_api.fetch_movie_details(movie_name)
        if movie_data is None:
            flash('Movie not found. Please check the title and try again.', 'error')
        else:
            data_manager.add_to_watchlist(user_id, movie_data)
            flash('Movie added successfully to your watchlist!', 'success')
    except DuplicateMovieError as e:
        flash(str(e), 'error')
    return redirect(request.referrer)


@app.errorhandler(404)
def page_not_found():
    """Render the custom 404 error page."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
