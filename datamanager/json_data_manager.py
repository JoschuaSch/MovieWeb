import json
import logging
from retrying import retry
from .data_manager_interface import DataManagerInterface
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry parameters
try_again_in = 1000
max_attempts = 3


class UserNotFoundError(Exception):
    """Raised when a user is not found in the data."""
    pass


class MovieNotFoundError(Exception):
    """Raised when a movie is not found in a user's list."""
    pass


class DuplicateMovieError(Exception):
    """Raised when a movie is already in the user's list."""
    pass


class JSONDataManager(DataManagerInterface):
    def __init__(self, filename):
        self.filename = filename
        self.users = {}
        self.load_from_file()

    @retry(stop_max_attempt_number=max_attempts, wait_fixed=try_again_in)
    def load_from_file(self):
        try:
            with open(self.filename, 'r') as f:
                self.users = json.load(f)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"An error occurred while loading the file: {e}")
            raise

    @retry(stop_max_attempt_number=max_attempts, wait_fixed=try_again_in)
    def save_to_file(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"An error occurred while saving to the file: {e}")
            raise

    def get_all_users(self):
        try:
            return [{'id': user_id, **user_data} for user_id, user_data in self.users.items()]
        except Exception as e:
            logger.error(f"An error occurred while getting all users: {e}")
            return []

    def get_user_movies(self, user_id):
        try:
            user = self.users.get(user_id)
            if user:
                return [(movie_id, details) for movie_id, details in user["movies"].items()]
        except Exception as e:
            logger.error(f"An error occurred while retrieving user movies: {e}")
        return []

    def add_user(self, user_id, name, password_hash, age=None, favorite_movie=None, favorite_quote=None,
                 words_to_live_by=None, sex=None, profile_picture=None):
        try:
            if user_id not in self.users:
                self.users[user_id] = {
                    "name": name,
                    "password": password_hash,
                    "movies": {},
                    "age": age,
                    "favorite_movie": favorite_movie,
                    "favorite_quote": favorite_quote,
                    "words_to_live_by": words_to_live_by,
                    "sex": sex,
                    "profile_picture": profile_picture
                }
                self.save_to_file()
            else:
                print("User ID already exists.")
        except Exception as e:
            logger.error(f"An error occurred while adding the user: {e}")

    def add_movie(self, user_id, movie_details):
        user = self.users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found.")
        for movie in user["movies"].values():
            if movie["Title"] == movie_details["Title"]:
                raise DuplicateMovieError(f"You have already added '{movie_details['Title']}' to your list.")
        movie_details.setdefault('personal_rating', None)
        movie_details.setdefault('watched', False)
        unique_movie_id = str(uuid.uuid4())
        user["movies"][unique_movie_id] = movie_details
        self.save_to_file()
        return unique_movie_id

    def find_user_by_id(self, user_id):
        try:
            user = self.users.get(user_id, None)
            if user:
                return user
        except Exception as e:
            logger.error(f"An error occurred while finding the user: {e}")
            return None

    def find_movie_by_id(self, user_id, movie_id):
        try:
            user = self.find_user_by_id(user_id)
            if user:
                return user["movies"].get(movie_id, None)
        except Exception as e:
            logger.error(f"An error occurred while finding the movie: {e}")
            return None

    def update_movie(self, user_id, movie_id, new_details):
        user = self.users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found.")
        movie = user["movies"].get(movie_id)
        if not movie:
            raise MovieNotFoundError(f"Movie with ID {movie_id} not found for user with ID {user_id}.")
        movie.update(new_details)
        self.save_to_file()

    def delete_movie(self, user_id, movie_id):
        user = self.users.get(user_id)
        if user:
            if movie_id in user["movies"]:
                del user["movies"][movie_id]
                self.save_to_file()
            else:
                raise MovieNotFoundError(f"Movie with ID {movie_id} not found for user with ID {user_id}.")
        else:
            raise UserNotFoundError(f"User with ID {user_id} not found.")

    def movie_exists(self, user_id, movie_title):
        user = self.users.get(user_id)
        if user:
            for movie in user["movies"].values():
                if movie["Title"].lower() == movie_title.lower():
                    return True
        return False

    def get_most_watched_movies(self):
        movie_watches = {}
        for user in self.users.values():
            for movie_id, movie in user['movies'].items():
                if movie['Title'] not in movie_watches:
                    movie_watches[movie['Title']] = movie
                    movie_watches[movie['Title']]['watch_count'] = 0
                if movie['watched']:
                    movie_watches[movie['Title']]['watch_count'] += 1
        most_watched_movies = sorted(movie_watches.values(), key=lambda movies: movies['watch_count'], reverse=True)
        return most_watched_movies[:100]

    def search_users(self, query):
        return [{'id': user_id, **user_data} for user_id, user_data in self.users.items() if
                query.lower() in user_data['name'].lower()]

    def get_users_by_name(self, search):
        users = self.get_all_users()
        users = [user for user in users if search.lower() == user['name'].lower()]
        users.sort(key=lambda user: user['name'])
        return users

    def like_review(self, user_id, movie_id, liker_id):
        user = self.users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found.")
        movie = user["movies"].get(movie_id)
        if not movie:
            raise MovieNotFoundError(f"Movie with ID {movie_id} not found for user with ID {user_id}.")
        if "likes" not in movie or not isinstance(movie["likes"], dict):
            movie["likes"] = {"count": 0, "users": []}
        if liker_id in movie["likes"]["users"]:
            return
        movie["likes"]["count"] += 1
        movie["likes"]["users"].append(liker_id)
        self.save_to_file()

    def update_user(self, user_id, new_details):
        user = self.users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found.")
        user.update(new_details)
        self.save_to_file()

    def delete_user(self, user_id):
        try:
            if user_id in self.users:
                user = self.users[user_id]
                profile_picture = user.get('profile_picture', None)
                if profile_picture and profile_picture != 'profile_pictures/placeholder.png':
                    try:
                        profile_picture_path = os.path.join(
                            'C:\\Users\\schro\\MovieWeb\\static\\User_picked_profile_pictures', profile_picture)
                        if os.path.isfile(profile_picture_path):
                            os.remove(profile_picture_path)
                    except Exception as e:
                        logger.error(f"An error occurred while deleting the profile picture: {e}")
                del self.users[user_id]
                self.save_to_file()
            else:
                raise UserNotFoundError(f"User with ID {user_id} does not exist.")
        except Exception as e:
            logger.error(f"An error occurred while deleting the user: {e}")
            raise
