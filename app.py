from flask import Flask, render_template, request, redirect, url_for, flash
from datamanager.json_data_manager import JSONDataManager, UserNotFoundError, MovieNotFoundError
import uuid
from werkzeug.exceptions import BadRequest
import omdb_api

app = Flask(__name__)
app.secret_key = 'Hello@@'
data_manager = JSONDataManager('data.json')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/users/<user_id>')
def user_movies(user_id):
    try:
        movies = data_manager.get_user_movies(user_id)
        return render_template('user_movies.html', movies=movies)
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
        if not name or len(name) > 100:
            raise BadRequest('Invalid user name.')
        user_id = str(uuid.uuid4())
        data_manager.add_user(user_id, name)
        return redirect(url_for('list_users'))
    return render_template('add_user.html')


@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        user_id = request.form['user_id']
        movie_name = request.form['movie_name']
        personal_rating = request.form.get('rating')
        watched = 'watched' in request.form
        existing_movies = data_manager.get_user_movies(user_id)
        if any(movie['Title'] == movie_name for movie in existing_movies):
            flash('Movie already exists in the user\'s movie list.')
            return redirect(url_for('add_movie', user_id=user_id))
        movie_details = omdb_api.fetch_movie_details(movie_name)
        if movie_details is None:
            flash('Movie not found. Please check the movie name and try again.')
            return redirect(url_for('add_movie', user_id=user_id))
        else:
            movie_details['personal_rating'] = personal_rating
            movie_details['watched'] = watched
            movie_id = data_manager.add_movie(user_id, movie_id=None, movie_details=movie_details)
            return render_template('confirm_movie.html', user_id=user_id, movie_id=movie_id, movie=movie_details)
    else:
        users = data_manager.get_all_users()
        return render_template('add_movie.html', users=users)


@app.route('/confirm_movie', methods=['POST'])
def confirm_movie():
    movie_title = request.form['title']
    movie_data = omdb_api.fetch_movie_details(movie_title)
    if movie_data is None:
        flash('Movie not found. Please check the title and try again.')
        return redirect(url_for('add_movie'))
    else:
        return render_template('confirm_movie.html', movie=movie_data)


@app.route('/users/<user_id>/movies/update/<movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    if request.method == 'POST':
        movie_name = request.form['name']
        movie_director = request.form['director']
        movie_year = int(request.form['year'])
        movie_rating = float(request.form.get('rating'))
        watched = 'watched' in request.form
        movie_details = {
            "Title": movie_name,
            "Director": movie_director,
            "Year": movie_year,
            "personal_rating": movie_rating,
            "watched": watched
        }
        try:
            data_manager.update_movie(user_id, movie_id, movie_details)
        except (UserNotFoundError, MovieNotFoundError) as e:
            return render_template('error.html', message=str(e)), 404
        return redirect(url_for('user_movies', user_id=user_id))
    else:
        try:
            movie = data_manager.find_movie_by_id(user_id, movie_id)
        except (UserNotFoundError, MovieNotFoundError) as e:
            return render_template('error.html', message=str(e)), 404
        return redirect(url_for('update_movie', user_id=user_id, movie_id=movie_id, movie=movie))


@app.route('/users/<user_id>/delete_movie/<movie_id>', methods=['POST'])
def delete_movie(user_id, movie_id):
    try:
        data_manager.delete_movie(user_id, movie_id)
        return redirect(url_for('user_movies', user_id=user_id))
    except ValueError as e:
        return render_template('error.html', message=str(e)), 400


@app.route('/confirm_movie_for_user', methods=['POST'])
def confirm_movie_for_user():
    user_id = request.form['user_id']
    movie_name = request.form['movie_name']
    movie_data = omdb_api.fetch_movie_details(movie_name)
    if movie_data is None:
        flash('Movie not found. Please check the movie name and try again.')
        return redirect(url_for('add_movie'))
    else:
        return render_template('confirm_movie.html', user_id=user_id, movie=movie_data)


@app.route('/users/<user_id>/add_confirmed_movie/', methods=['POST'])
def add_confirmed_movie(user_id):
    try:
        data_manager.find_user_by_id(user_id)
    except UserNotFoundError:
        flash('User not found. Please check the user id and try again.')
        return redirect(url_for('home'))
    movie_data = request.form
    keys_of_interest = ['Title', 'Year', 'Rated', 'Director', 'Actors', 'Plot', 'Language', 'Country', 'Awards',
                        'Poster', 'imdbRating']
    movie = {key: movie_data.get(key, None) for key in keys_of_interest}
    movie_id = movie['Title'].replace(' ', '_') if movie.get('Title') else None
    data_manager.add_movie(user_id, movie_id, movie)
    flash('Movie successfully added!')
    return redirect(url_for('user_movies', user_id=user_id))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)