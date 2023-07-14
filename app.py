from flask import Flask, render_template, request, redirect, url_for, flash
from datamanager.json_data_manager import JSONDataManager, UserNotFoundError, MovieNotFoundError, DuplicateMovieError
import uuid
from werkzeug.exceptions import BadRequest, abort
import omdb_api
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
data_manager = JSONDataManager('data.json')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/users/<user_id>/movies')
@login_required
def user_movies(user_id):
    if current_user.id != user_id:
        return abort(403)
    try:
        movies = data_manager.get_user_movies(user_id)
        return render_template('user_movies.html', movies=movies, user_id=user_id)
    except UserNotFoundError:
        return f"User with ID {user_id} not found."


@app.route('/users')
def list_users():
    users = data_manager.get_all_users()
    return render_template('users.html', users=users)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
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
def add_movie():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        movie_name = request.form.get('movie_name')
        if not movie_name:
            flash('No movie name provided. Please check and try again.')
            return redirect(url_for('add_movie'))
        else:
            return redirect(url_for('confirm_movie', user_id=user_id, movie_name=movie_name))
    else:
        users = data_manager.get_all_users()
        return render_template('add_movie.html', users=users)


@app.route('/confirm_movie/<user_id>/<movie_name>', methods=['GET', 'POST'])
def confirm_movie(user_id, movie_name):
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
def update_movie(user_id, movie_id):
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
        except (UserNotFoundError, MovieNotFoundError) as e:
            return render_template('error.html', message=str(e)), 404
        return redirect(url_for('user_movies', user_id=user_id))
    else:
        return render_template('update_movie.html', user_id=user_id, movie_id=movie_id, movie=movie)


@app.route('/users/<user_id>/delete_movie/<movie_id>', methods=['POST'])
def delete_movie(user_id, movie_id):
    try:
        data_manager.delete_movie(user_id, movie_id)
        flash('Movie deleted successfully.')
        return redirect(url_for('user_movies', user_id=user_id))
    except ValueError as e:
        return render_template('error.html', message=str(e)), 400


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        user_data = data_manager.find_user_by_id(user_id)
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_id, user_data['name'])
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('user_movies', user_id=user_id))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('home'))


@app.route('/top100')
def top_100_movies():
    movies = data_manager.get_most_watched_movies()
    return render_template('top100.html', movies=movies)


if __name__ == '__main__':
    app.run(debug=True)
