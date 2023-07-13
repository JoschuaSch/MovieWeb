from abc import ABC, abstractmethod


class DataManagerInterface(ABC):
    @abstractmethod
    def get_all_users(self):
        """Return a list of all users"""
        pass

    @abstractmethod
    def get_user_movies(self, user_id):
        """Return a list of movies for a given user"""
        pass

    @abstractmethod
    def add_user(self, user_id, name):
        """Add a new user"""
        pass

    @abstractmethod
    def delete_user(self, user_id):
        """Delete a user"""
        pass

    @abstractmethod
    def add_movie(self, user_id, movie_id, movie_details):
        """Add a movie to a user's list"""
        pass

    @abstractmethod
    def delete_movie(self, user_id, movie_id):
        """Delete a movie from a user's list"""
        pass

    @abstractmethod
    def find_user_by_id(self, user_id):
        """Find and return a user by their id"""
        pass

    @abstractmethod
    def find_movie_by_id(self, user_id, movie_id):
        """Find and return a movie by their id for a given user"""
        pass
