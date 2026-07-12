import os
import pickle
import time
import pandas as pd
import requests
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -------------------- Load Data Dynamically --------------------
def download_file(url, output_name):
    if not os.path.exists(output_name):
        with st.spinner(f"Downloading data file ({output_name}). Please wait..."):
            response = requests.get(url)
            with open(output_name, "wb") as f:
                f.write(response.content)


# We ONLY need the movies data file now. No more huge similarity matrix!
MOVIES_URL = "https://drive.google.com/uc?export=download&id=1lJC4ju93UftB8qOcM8J04LBEcUZnW8s_"
download_file(MOVIES_URL, "movies_dict.pkl")

movies_dict = pickle.load(open("movies_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)


# -------------------- Smart On-Demand Recommender --------------------
def recommend(movie):
    # Vectorize tags dynamically for matching
    tfidf = TfidfVectorizer(max_features=5000, stop_words="english")

    # Check if 'tags' exists, fallback to 'string' or similar if needed
    tag_column = 'tags' if 'tags' in movies.columns else movies.columns[-1]
    tfidf_matrix = tfidf.fit_transform(movies[tag_column])

    movie_index = movies[movies["title"] == movie].index[0]

    # Compute similarity ONLY for the selected movie against all others
    # This prevents the 1GB RAM memory spike completely!
    selected_movie_vector = tfidf_matrix[movie_index]
    similarity_scores = cosine_similarity(selected_movie_vector, tfidf_matrix).flatten()

    distances = sorted(list(enumerate(similarity_scores)), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]]["movie_id"]
        title = movies.iloc[i[0]]["title"]
        recommended_movie_names.append(title)
        recommended_movie_posters.append(fetch_poster(movie_id))

    return recommended_movie_names, recommended_movie_posters


# -------------------- TMDB Settings --------------------
API_KEY = st.secrets["TMDB_API_KEY"]
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}


def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    for attempt in range(3):
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get("poster_path")
            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path
            return "https://via.placeholder.com/500x750?text=No+Poster"
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    return "https://via.placeholder.com/500x750?text=Error"


# -------------------- Modern UI Configurations --------------------
st.set_page_config(page_title="CineMatch | Movie Recommender", page_icon="🎬", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0c20 0%, #15102a 50%, #060214 100%);
    }
    .main-title {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3rem !important;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 5px;
        letter-spacing: -1px;
    }
    .sub-title {
        font-family: 'Inter', sans-serif;
        color: #8b85b1;
        text-align: center;
        margin-bottom: 40px;
        font-size: 1.1rem;
    }
    .movie-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, border 0.3s ease;
    }
    .movie-card:hover {
        transform: translateY(-8px);
        border: 1px solid rgba(138, 43, 226, 0.6);
    }
    .movie-title {
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        margin-top: 10px;
        word-wrap: break-word;
    }
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #7928CA 0%, #FF0080 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        transition: opacity 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        opacity: 0.9;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🎬 CineMatch AI</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Your ultimate companion for discovering cinematic masterpieces</p>',
            unsafe_allow_html=True)

left_spacer, center_col, right_spacer = st.columns([1, 2, 1])

with center_col:
    movie_list = movies["title"].values
    selected_movie = st.selectbox(
        "Type or select a movie from the catalog:", movie_list, label_visibility="collapsed"
    )

    btn_spacer_l, btn_col, btn_spacer_r = st.columns([1.2, 1, 1])
    with btn_col:
        submit_button = st.button("Generate Picks")

if submit_button:
    names, posters = recommend(selected_movie)
    st.markdown("<br><br>", unsafe_allow_html=True)

    cols = st.columns(5, gap="medium")
    for i in range(5):
        with cols[i]:
            st.markdown(f"""
                <div class="movie-card">
                    <img src="{posters[i]}" style="width:100%; border-radius:12px; aspect-ratio:2/3; object-fit:cover;"/>
                    <div class="movie-title">{names[i]}</div>
                </div>
            """, unsafe_allow_html=True)