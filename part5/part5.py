import streamlit as st
import pandas as pd
import numpy as np
import sqlite3 as sql
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from collections import Counter

# Page config
st.set_page_config(page_title="Spotify Dashboard", page_icon="🎵", layout="wide")

# Spotify styling
st.markdown("""
    <style>
    .stApp { background-color: #191414; color: white; }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
    .stApp { background-color: #191414; color: white; }
    [data-testid="stMetric"] { background-color: #1DB954; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricLabel"] { color: white !important; }
    [data-testid="stMetricValue"] { color: white !important; }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/artist_data.csv")
    df = df[(df["followers"] > 0) & (df["artist_popularity"] > 0) & (df["name"] != "Various Artists")]
    df["log_followers"] = np.log1p(df["followers"])
    return df


@st.cache_data
def load_db():
    conn = sql.connect("data/spotify_database.db")
    tracks = pd.read_sql("SELECT * FROM tracks_data", conn)
    albums = pd.read_sql("SELECT * FROM albums_data", conn)
    conn.close()
    return tracks, albums

df = load_data()
tracks, albums = load_db()

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", ["Overview", "Genre Explorer", "Artist Search"])

if page == "Overview":
    st.title("🎵 Spotify Artist Dashboard")
    st.write("General statistics of the dataset")

elif page == "Genre Explorer":
    st.title("🎸 Genre Explorer")

elif page == "Artist Search":
    st.title("🔍 Artist Search")

if page == "Overview":

    # Numerical stats in 3 columns
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Artists", df["name"].nunique())
    col2.metric("Average Popularity", round(df["artist_popularity"].mean(), 1))
    col3.metric("Most Followed Artist", df.loc[df["followers"].idxmax(), "name"])

    st.divider()

# Itried doing it with functions but i cant get this to work anyone has any ideas?
#from intro.py import plot_top_popularity, plot_top_followers

#import sys
#sys.path.append("part1")
#from intro import plot_popularity, plot_followers

#import sys
#import os
#sys.path.append(os.path.join(os.path.dirname(__file__), "..", "part1"))
#from intro.py import plot_popularity, plot_followers

col_left, col_right = st.columns(2)

# Top 10 by popularity
with col_left:
    st.subheader("Top 10 Artists by Popularity")
    top_popularity = df.nlargest(10, "artist_popularity")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top_popularity["name"], top_popularity["artist_popularity"], color="#1DB954")
    ax.set_xlabel("Popularity score (0-100)")
    ax.invert_yaxis()
    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    st.pyplot(fig)

# Top 10 by followers
with col_right:
    st.subheader("Top 10 Artists by Followers")
    top_followers = df.nlargest(10, "followers").copy()
    top_followers["followers_m"] = top_followers["followers"] / 1_000_000
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.barh(top_followers["name"], top_followers["followers_m"], color="#1DB954")
    ax2.set_xlabel("Followers (millions)")
    ax2.invert_yaxis()
    fig2.patch.set_facecolor("#191414")
    ax2.set_facecolor("#191414")
    ax2.tick_params(colors="white")
    ax2.xaxis.label.set_color("white")
    st.pyplot(fig2)