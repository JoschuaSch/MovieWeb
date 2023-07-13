import csv
import logging
from retrying import retry
from .data_manager_interface import DataManagerInterface

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry parameters
try_again_in = 1000
max_attempts = 3


class CSVDataManager(DataManagerInterface):
    def __init__(self, filename):
        self.filename = filename
        self.users = {}
        self.load_from_file()

    @retry(stop_max_attempt_number=max_attempts, wait_fixed=try_again_in)
    def load_from_file(self):
        try:
            with open(self.filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user_id = row['user_id']
                    name = row['name']
                    self.users[user_id] = {'name': name, 'movies': {}}
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"An error occurred while loading the file: {e}")
            raise

    @retry(stop_max_attempt_number=max_attempts, wait_fixed=try_again_in)
    def save_to_file(self):
        try:
            with open(self.filename, 'w') as f:
                writer = csv.DictWriter(f, fieldnames=['user_id', 'name'])
                writer.writeheader()
                for user_id, user in self.users.items():
                    writer.writerow({'user_id': user_id, 'name': user['name']})
        except Exception as e:
            logger.error(f"An error occurred while saving to the file: {e}")
            raise

    def get_all_users(self):
        return list(self.users.values())

    def get_user_movies(self, user_id):
        user = self.users.get(user_id)
        if user:
            return list(user["movies"].values())
        return []

    def add_user(self, user_id, name):
        try:
            if user_id not in self.users:
                self.users[user_id] = {"id": user_id, "name": name, "movies": {}}
                self.save_to_file()
            else:
                raise ValueError("User ID already exists.")
        except Exception as e:
            logger.error(f"An error occurred while adding a user: {e}")
            raise

    def delete_user(self, user_id):
        try:
            if user_id in self.users:
                del self.users[user_id]
                self.save_to_file()
            else:
                raise ValueError("User ID does not exist.")
        except Exception as e:
            logger.error(f"An error occurred while deleting a user: {e}")
            raise

    def add_movie(self, user_id, movie_id, movie_details):
        try:
            user = self.users.get(user_id)
            if user:
                if movie_id not in user["movies"]:
                    user["movies"][movie_id] = movie_details
                    self.save_to_file()
                else:
                    raise ValueError("Movie ID already exists for this user.")
            else:
                raise ValueError("User ID does not exist.")
        except Exception as e:
            logger.error(f"An error occurred while adding a movie: {e}")
            raise

    def delete_movie(self, user_id, movie_id):
        try:
            user = self.users.get(user_id)
            if user:
                if movie_id in user["movies"]:
                    del user["movies"][movie_id]
                    self.save_to_file()
                else:
                    raise ValueError("Movie ID does not exist for this user.")
            else:
                raise ValueError("User ID does not exist.")
        except Exception as e:
            logger.error(f"An error occurred while deleting a movie: {e}")
            raise

    def find_user_by_id(self, user_id):
        try:
            user = self.users.get(user_id, None)
            if user is None:
                logger.warning(f"User with ID {user_id} not found.")
            return user
        except Exception as e:
            logger.error(f"An error occurred while finding a user by ID: {e}")
            raise

    def find_movie_by_id(self, user_id, movie_id):
        try:
            user = self.find_user_by_id(user_id)
            if user:
                movie = user["movies"].get(movie_id, None)
                if movie is None:
                    logger.warning(f"Movie with ID {movie_id} for user {user_id} not found.")
                return movie
            else:
                return None
        except Exception as e:
            logger.error(f"An error occurred while finding a movie by ID: {e}")
            raise
