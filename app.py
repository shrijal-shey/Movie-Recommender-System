import pandas as pd
import streamlit as st
import pickle
import requests
import time

# -------------------- Load Data --------------------
movies_dict = pickle.load(open("movies_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))

# -------------------- TMDB Settings --------------------
API_KEY = "1036579557f818a578b0bc05e59640bc"

session = requests.Session()

headers = {
    "User-Agent": "Mozilla/5.0"
}

# -------------------- Fetch Poster --------------------
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    for attempt in range(3):   # Retry 3 times
        try:
            response = session.get(
                url,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            print(f"Movie ID: {movie_id}")
            print(data)
            print("=" * 60)

            poster_path = data.get("poster_path")

            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path
            else:
                print(f"No poster found for {movie_id}")
                return "https://via.placeholder.com/500x750?text=No+Poster"

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1} failed for Movie ID {movie_id}")
            print(e)
            time.sleep(1)

    return "https://via.placeholder.com/500x750?text=Error"

# -------------------- Recommendation --------------------
def recommend(movie):

    movie_index = movies[movies["title"] == movie].index[0]

    distances = sorted(
        list(enumerate(similarity[movie_index])),
        reverse=True,
        key=lambda x: x[1]
    )

    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:

        movie_id = movies.iloc[i[0]]["movie_id"]
        title = movies.iloc[i[0]]["title"]

        print(f"Title : {title}")
        print(f"Movie ID : {movie_id}")
        print("-" * 40)

        recommended_movie_names.append(title)
        recommended_movie_posters.append(fetch_poster(movie_id))

    return recommended_movie_names, recommended_movie_posters

# -------------------- Streamlit UI --------------------
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Movie Recommender System")

movie_list = movies["title"].values

selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button("Show Recommendation"):

    names, posters = recommend(selected_movie)

    cols = st.columns(5)

    for i in range(5):
        with cols[i]:
            st.write(f"**{names[i]}**")
            st.image(posters[i], width="stretch")