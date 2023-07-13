import json
import logging
from retrying import retry
from .data_manager_interface import DataManagerInterface
import uuid

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
                return list(user["movies"].values())
        except Exception as e:
            logger.error(f"An error occurred while retrieving user movies: {e}")
        return []

    def add_user(self, user_id, name):
        try:
            if user_id not in self.users:
                self.users[user_id] = {"name": name, "movies": {}}
                self.save_to_file()
            else:
                print("User ID already exists.")
        except Exception as e:
            logger.error(f"An error occurred while adding the user: {e}")

    def delete_user(self, user_id):
        try:
            if user_id in self.users:
                del self.users[user_id]
                self.save_to_file()
            else:
                print("User ID does not exist.")
        except Exception as e:
            logger.error(f"An error occurred while deleting the user: {e}")

    def add_movie(self, user_id, movie_id, movie_details):
        user = self.users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found.")
        if movie_id in user["movies"]:
            raise ValueError(f"Movie with ID {movie_id} already exists for this user.")
        movie_details.setdefault('personal_rating', None)
        movie_details.setdefault('watched', False)
        unique_movie_id = str(uuid.uuid4())
        user["movies"][unique_movie_id] = movie_details
        self.save_to_file()
        return unique_movie_id

    def delete_movie(self, user_id, movie_id):
        try:
            user = self.users.get(user_id)
            if user:
                if movie_id in user["movies"]:
                    del user["movies"][movie_id]
                    self.save_to_file()
                else:
                    print("Movie ID does not exist for this user.")
            else:
                print("User ID does not exist.")
        except Exception as e:
            logger.error(f"An error occurred while deleting the movie: {e}")

    def find_user_by_id(self, user_id):
        try:
            return self.users.get(user_id, None)
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

    def update_movie(self, user_id, movie_id, movie_details):
        user = self.users.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found.")
        if movie_id not in user["movies"]:
            raise MovieNotFoundError(f"Movie with ID {movie_id} not found for user with ID {user_id}.")
        movie_details['personal_rating'] = movie_details.get('personal_rating',
                                                             user["movies"][movie_id].get('personal_rating'))
        movie_details['watched'] = movie_details.get('watched', user["movies"][movie_id].get('watched'))
        user["movies"][movie_id] = movie_details
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