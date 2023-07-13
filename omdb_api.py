import requests


def fetch_movie_details(movie_title):
    api_key = '95e83589'
    base_url = f'http://www.omdbapi.com/?apikey={api_key}&t={movie_title}'
    try:
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f'Failed to fetch movie details for {movie_title}. Error: {str(e)}')
        return None

    movie_details = response.json()
    return movie_details
