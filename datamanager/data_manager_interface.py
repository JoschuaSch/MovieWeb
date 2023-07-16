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
    def add_user(self, user_id, name, password_hash):
        """Add a new user"""
        pass

    @abstractmethod
    def delete_user(self, user_id):
        """Delete a user"""
        pass

    @abstractmethod
    def add_movie(self, user_id, movie_details):
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

    @abstractmethod
    def get_most_watched_movies(self):
        """Return the list of most watched movies"""
        pass

    @abstractmethod
    def get_reviews_sorted_by_likes(self):
        """Return the list of reviews sorted by likes"""
        pass

    @abstractmethod
    def get_reviews_sorted_by_date(self):
        """Return the list of reviews sorted by date"""
        pass

    @abstractmethod
    def add_to_watchlist(self, user_id, movie_details):
        """Add a movie to the user's watchlist"""
        pass

    @abstractmethod
    def mark_as_watched(self, user_id, movie_id):
        """Mark a movie as watched for a user"""
        pass

    @abstractmethod
    def mark_as_unwatched(self, user_id, movie_id):
        """Mark a movie as unwatched for a user"""
        pass

    @abstractmethod
    def get_user_watchlist(self, user_id):
        """Return a user's watchlist"""
        pass
