import os
import pickle
import time
import pandas as pd
import requests
import streamlit as st

# -------------------- Load Data Dynamically --------------------
# Helper function to download large files from Google Drive if they don't exist locally
def download_file(url, output_name):
    if not os.path.exists(output_name):
        with st.spinner(f"Downloading data file ({output_name}). Please wait..."):
            response = requests.get(url)
            with open(output_name, "wb") as f:
                f.write(response.content)

# Your converted Google Drive Direct Download Links
MOVIES_URL = "https://drive.google.com/uc?export=download&id=1lJC4ju93UftB8qOcM8J04LBEcUZnW8s_"
SIMILARITY_URL = "https://drive.google.com/uc?export=download&id=1qBTcVgcYs8qoRf9dK4LGiYhbJT6iRdpK"

# Fetch datasets onto the cloud environment
download_file(MOVIES_URL, "movies_dict.pkl")
download_file(SIMILARITY_URL, "similarity.pkl")

# Load files
movies_dict = pickle.load(open("movies_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))

# -------------------- TMDB Settings --------------------
# Securely pulls the key from Streamlit Cloud's Advanced Settings
API_KEY = st.secrets["TMDB_API_KEY"]

session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}


# -------------------- Fetch Poster --------------------
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"

    for attempt in range(3):  # Retry 3 times
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            poster_path = data.get("poster_path")

            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path
            else:
                return "https://via.placeholder.com/500x750?text=No+Poster"

        except requests.exceptions.RequestException as e:
            time.sleep(1)

    return "https://via.placeholder.com/500x750?text=Error"


# -------------------- Recommendation --------------------
def recommend(movie):
    movie_index = movies[movies["title"] == movie].index[0]

    distances = sorted(
        list(enumerate(similarity[movie_index])),
        reverse=True,
        key=lambda x: x[1],
    )

    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]]["movie_id"]
        title = movies.iloc[i[0]]["title"]

        recommended_movie_names.append(title)
        recommended_movie_posters.append(fetch_poster(movie_id))

    return recommended_movie_names, recommended_movie_posters


# -------------------- Streamlit UI --------------------
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

st.title("🎬 Movie Recommender System")

movie_list = movies["title"].values

selected_movie = st.selectbox(
    "Type or select a movie from the dropdown", movie_list
)

if st.button("Show Recommendation"):
    names, posters = recommend(selected_movie)

    cols = st.columns(5)

    for i in range(5):
        with cols[i]:
            st.write(f"**{names[i]}**")
            st.image(posters[i], use_container_width=True)