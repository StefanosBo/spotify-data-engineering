"""
Part 5: Spotify Analytics Dashboard
=====================================
This dashboard reuses functions from earlier parts of the project:
  - Part 1 (part1_functions.py): Artist exploratory analysis
  - Part 3 (db_utils, album_features, collaborations, task_eras,
            task_explicit_collabs, popularity): Database queries & analysis
  - Part 4 (spotify_wrangle): Data wrangling, outlier detection, era analysis

Run with:  streamlit run dashboard.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import sys

# ──────────────────────────────────────────────────────────────────
# Path setup - make all project parts importable 
# ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # part5/
sys.path.insert(0, os.path.join(PROJECT_ROOT, "part3"))          # part3/
sys.path.insert(0, os.path.join(PROJECT_ROOT, "part4"))          # part4/

# ──────────────────────────────────────────────────────────────────
# Part 1 imports
# ──────────────────────────────────────────────────────────────────
from part1_functions import (
    load_data,
    get_top_popularity,
    get_top_followers,
    plot_popularity,
    plot_followers,
    get_correlation,
    plot_popularity_vs_followers,
    get_overperformers_and_legacy,
    plot_overperformers_legacy,
    get_num_genres_summary,
    plot_num_genres_vs_popularity,
    plot_num_genres_vs_followers,
    plot_follower_groups_vs_popularity,
)

# ──────────────────────────────────────────────────────────────────
# Part 3 imports
# ──────────────────────────────────────────────────────────────────
from db_utils import get_data
from album_features import analyze_album_consistency
from collaborations import analyze_collaborations
from task_eras import categorize_eras
from task_explicit_collabs import analyze_explicit_tracks
from popularity import analyze_popularity

# ──────────────────────────────────────────────────────────────────
# Part 4 imports
# ──────────────────────────────────────────────────────────────────
from spotify_wrangle import (
    load_all_tables,
    clean_data,
    detect_outliers_iqr,
    add_era_column,
    album_feature_summary,
    get_era_features,
)

# ──────────────────────────────────────────────────────────────────
# Constants & helpers
# ──────────────────────────────────────────────────────────────────
SPOTIFY_GREEN = "#1DB954"
LIGHT_GREEN = "#1ed760"          
SOFT_GREEN = "#158f3b"
SPOTIFY_DARK = "#191414"
ACCENT_BLUE = "#4A90D9"
ACCENT_CORAL = "#E8555A"
ACCENT_PURPLE = "#9B59B6"
ACCENT_AMBER = "#F39C12"           
PALETTE = [SPOTIFY_GREEN, ACCENT_BLUE, ACCENT_CORAL, ACCENT_PURPLE, ACCENT_AMBER,
           "#2ECC71", "#3498DB", "#E74C3C", "#8E44AD", "#F1C40F"]
AUDIO_FEATURES = ["danceability", "energy", "speechiness", "acousticness",
                   "instrumentalness", "liveness", "valence"]
AUDIO_FEATURES_FULL = AUDIO_FEATURES + ["loudness", "tempo"]

DARK_CSS = """
<style>
    .stApp { background-color: #191414; color: white; }
    [data-testid="stSidebar"] { background-color: #121212; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stMetric"] {
        background-color: #1DB954; border-radius: 10px; padding: 10px;
    }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] { color: white !important; }
    h1, h2, h3 { color: white !important; }
</style>
"""

def style_fig(fig, title="", height=450):
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color="white")),
        template="plotly_dark", height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(size=12, color="white"), colorway=PALETTE,
        paper_bgcolor=SPOTIFY_DARK, plot_bgcolor="#121212",
    )
    return fig


def fmt(n):
    if n >= 1_000_000: return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:     return f"{n / 1_000:.1f}K"
    return str(int(n))


# Cached loaders using Part 1 and Part 4 functions
@st.cache_data
def cached_load_artist_data():
    return load_data()              # Part 1

@st.cache_data
def cached_load_all():
    return load_all_tables()        # Part 4

@st.cache_data
def cached_clean_data(_tracks, _features, _albums):
    return clean_data(_tracks, _features, _albums)  # Part 4


# ══════════════════════════════════════════════════════════════════
# PAGE 1: OVERVIEW
# Uses: Part 1 (load_data, plot_popularity, plot_followers, get_top_*)
#       Part 3 (get_data for DB-level stats)
# ══════════════════════════════════════════════════════════════════
def page_overview():
    st.title("🎵 Spotify Database Overview")
    st.markdown("Key statistics from the research carried out throughout the project.")

    # Part 1: artist-level stats
    df = cached_load_artist_data()
    top_pop = get_top_popularity(df)        # Part 1
    top_fol = get_top_followers(df)         # Part 1

    # Part 3: database-level stats via get_data
    stats = get_data("""
        SELECT
            (SELECT COUNT(*) FROM tracks_data) AS total_tracks,
            (SELECT COUNT(DISTINCT album_id) FROM albums_data) AS total_albums,
            (SELECT AVG(track_popularity) FROM tracks_data) AS avg_track_pop,
            (SELECT ROUND(100.0 * SUM(CASE WHEN explicit='true' THEN 1 ELSE 0 END)
                    / COUNT(*), 1) FROM tracks_data) AS explicit_pct
    """)

    # Numerical summary
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Artists", fmt(df["name"].nunique()))
    c2.metric("Tracks", fmt(stats["total_tracks"][0]))
    c3.metric("Albums", fmt(stats["total_albums"][0]))
    c4.metric("Avg Popularity", f"{stats['avg_track_pop'][0]:.1f}")
    c5.metric("Explicit %", f"{stats['explicit_pct'][0]}%")

    st.divider()

    # Graphical summary: Part 1 matplotlib plots
    st.subheader("Top Artists")
    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(plot_popularity(df))      # Part 1
    with col2:
        st.pyplot(plot_followers(df))       # Part 1

    # Additional charts via Part 3 get_data
    st.subheader("Database-Wide Distributions")
    col3, col4 = st.columns(2)
    with col3:
        pop = get_data("SELECT track_popularity FROM tracks_data")
        fig = px.histogram(pop, x="track_popularity", nbins=50,
                           color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, "Track Popularity Distribution")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        decades = get_data("""
            SELECT (CAST(SUBSTR(release_date,1,4) AS INTEGER)/10*10) AS decade,
                   COUNT(*) AS cnt
            FROM albums_data
            WHERE CAST(SUBSTR(release_date,1,4) AS INTEGER) >= 1950
            GROUP BY decade ORDER BY decade
        """)
        fig = px.bar(decades, x="decade", y="cnt",
                     color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, "Tracks by Decade")
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 2: FEATURE & GENRE EXPLORER
# Uses: Part 3 (get_data, analyze_explicit_tracks)
#       Part 4 (label_tracks_by_feature)
# Requirement: sidebar feature/genre selection
# ══════════════════════════════════════════════════════════════════
def page_feature_genre():
    st.title("🔍 Feature & Genre Explorer")
    st.sidebar.header("Explorer Options")
    mode = st.sidebar.radio("Explore by", ["Audio Feature", "Genre"])

    if mode == "Audio Feature":
        _explore_feature()
    else:
        _explore_genre()


def _explore_feature():
    selected = st.sidebar.selectbox("Select Feature", AUDIO_FEATURES_FULL)
    pop_range = st.sidebar.slider("Popularity Range", 0, 100, (0, 100))

    col1, col2 = st.columns(2)

    # Feature distribution via Part 3 get_data
    with col1:
        dist = get_data(f"SELECT [{selected}] FROM features_data "
                        "ORDER BY RANDOM() LIMIT 5000")
        fig = px.histogram(dist, x=selected, nbins=50,
                           color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, f"{selected.title()} Distribution")
        st.plotly_chart(fig, use_container_width=True)

    # Feature vs Popularity via Part 3 get_data
    with col2:
        scatter = get_data(f"""
            SELECT f.[{selected}], t.track_popularity
            FROM features_data f
            JOIN tracks_data t ON f.id = t.id
            WHERE t.track_popularity BETWEEN ? AND ?
            ORDER BY RANDOM() LIMIT 3000
        """, (pop_range[0], pop_range[1]))
        if not scatter.empty:
            fig = px.scatter(scatter, x=selected, y="track_popularity",
                             color_discrete_sequence=[SPOTIFY_GREEN], opacity=0.4)
            style_fig(fig, f"{selected.title()} vs Track Popularity")
            valid = scatter[[selected, "track_popularity"]].dropna()
            if len(valid) > 10:
                coeffs = np.polyfit(valid[selected], valid["track_popularity"], 1)
                xf = np.linspace(valid[selected].min(), valid[selected].max(), 100)
                fig.add_trace(go.Scatter(
                    x=xf, y=np.polyval(coeffs, xf), mode="lines",
                    line=dict(color="white", dash="dash"), name="Trend"))
            st.plotly_chart(fig, use_container_width=True)

    # Correlation heatmap via Part 3 get_data
    st.subheader("Feature Correlation Matrix")
    corr_data = get_data(
        f"SELECT {', '.join(AUDIO_FEATURES_FULL)} FROM features_data "
        "ORDER BY RANDOM() LIMIT 10000")
    fig = px.imshow(corr_data.corr(), text_auto=".2f",
                    color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
    style_fig(fig, "Audio Feature Correlations", height=500)
    st.plotly_chart(fig, use_container_width=True)


def _explore_genre():
    # Top genres via Part 3 get_data
    genres = get_data("""
        SELECT genre, COUNT(*) AS cnt FROM (
            SELECT genre_0 AS genre FROM artist_data WHERE genre_0 != '' AND genre_0 IS NOT NULL
            UNION ALL SELECT genre_1 FROM artist_data WHERE genre_1 != '' AND genre_1 IS NOT NULL
            UNION ALL SELECT genre_2 FROM artist_data WHERE genre_2 != '' AND genre_2 IS NOT NULL
            UNION ALL SELECT genre_3 FROM artist_data WHERE genre_3 != '' AND genre_3 IS NOT NULL
            UNION ALL SELECT genre_4 FROM artist_data WHERE genre_4 != '' AND genre_4 IS NOT NULL
        ) GROUP BY genre ORDER BY cnt DESC LIMIT 50
    """)
    selected_genre = st.sidebar.selectbox("Select Genre", genres["genre"].tolist())
    min_pop = st.sidebar.slider("Min Artist Popularity", 0, 100, 0)

    # Top artists via Part 3 get_data
    top = get_data("""
        SELECT a.name, a.artist_popularity, a.followers
        FROM artist_data a
        WHERE a.artist_popularity >= ?
          AND (a.genre_0=? OR a.genre_1=? OR a.genre_2=? OR a.genre_3=? OR a.genre_4=?)
        ORDER BY a.artist_popularity DESC LIMIT 15
    """, (min_pop, *([selected_genre] * 5)))

    if top.empty:
        st.warning("No artists found.")
        return

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(top, x="artist_popularity", y="name", orientation="h",
                     color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, f"Top Artists - {selected_genre}")
        fig.update_yaxes(autorange="reversed", title="")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        if (top["followers"] > 0).any():
            fig = px.scatter(top, x="followers", y="artist_popularity",
                             hover_name="name", log_x=True,
                             color_discrete_sequence=[SPOTIFY_GREEN])
            style_fig(fig, "Popularity vs Followers (log)")
            st.plotly_chart(fig, use_container_width=True)

    # Feature radar via Part 3 get_data
    gf = get_data("""
        SELECT AVG(f.danceability) AS danceability, AVG(f.energy) AS energy,
               AVG(f.speechiness) AS speechiness, AVG(f.acousticness) AS acousticness,
               AVG(f.instrumentalness) AS instrumentalness, AVG(f.liveness) AS liveness,
               AVG(f.valence) AS valence
        FROM features_data f
        JOIN albums_data al ON f.id = al.track_id
        JOIN artist_data a ON al.artist_id = a.id
        WHERE (a.genre_0=? OR a.genre_1=? OR a.genre_2=? OR a.genre_3=? OR a.genre_4=?)
    """, tuple([selected_genre] * 5))
    ov = get_data("""
        SELECT AVG(danceability) AS danceability, AVG(energy) AS energy,
               AVG(speechiness) AS speechiness, AVG(acousticness) AS acousticness,
               AVG(instrumentalness) AS instrumentalness, AVG(liveness) AS liveness,
               AVG(valence) AS valence
        FROM features_data
    """)

    col3, col4 = st.columns(2)
    with col3:
        gv = [gf[c][0] for c in AUDIO_FEATURES]
        ov_v = [ov[c][0] for c in AUDIO_FEATURES]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=gv+[gv[0]], theta=AUDIO_FEATURES+[AUDIO_FEATURES[0]],
                                      fill="toself", name=selected_genre, line_color=SPOTIFY_GREEN))
        fig.add_trace(go.Scatterpolar(r=ov_v+[ov_v[0]], theta=AUDIO_FEATURES+[AUDIO_FEATURES[0]],
                                      fill="toself", name="Overall", line_color=SOFT_GREEN, opacity=0.4))
        style_fig(fig, f"Audio Profile - {selected_genre}")
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])))
        st.plotly_chart(fig, use_container_width=True)

    # Explicit % - uses Part 3 analyze_explicit_tracks results pattern
    with col4:
        eg = get_data("""
            SELECT SUM(CASE WHEN t.explicit='true' THEN 1 ELSE 0 END) AS ex,
                   COUNT(*) AS tot
            FROM tracks_data t
            JOIN albums_data al ON t.id = al.track_id
            JOIN artist_data a ON al.artist_id = a.id
            WHERE (a.genre_0=? OR a.genre_1=? OR a.genre_2=? OR a.genre_3=? OR a.genre_4=?)
        """, tuple([selected_genre] * 5))
        eo = get_data("SELECT SUM(CASE WHEN explicit='true' THEN 1 ELSE 0 END) AS ex, COUNT(*) AS tot FROM tracks_data")
        gpct = 100.0 * eg["ex"][0] / max(eg["tot"][0], 1)
        opct = 100.0 * eo["ex"][0] / max(eo["tot"][0], 1)
        comp = pd.DataFrame({"Category": [selected_genre, "Overall"], "Explicit %": [gpct, opct]})
        fig = px.bar(comp, x="Category", y="Explicit %", color="Category",
                     color_discrete_sequence=[SPOTIFY_GREEN, SOFT_GREEN])
        style_fig(fig, "Explicit Content: Genre vs Overall")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 3: ARTIST SEARCH
# Uses: Part 1 (load_data, get_correlation)
#       Part 3 (get_data)
# Requirement: sidebar artist search for top 200
# ══════════════════════════════════════════════════════════════════
def page_artist_search():
    st.title("🔎 Artist Search")

    # Top 200 artists via Part 3 get_data
    artists = get_data("""
        SELECT id, name, artist_popularity, followers
        FROM artist_data
        WHERE artist_popularity >= 70
        ORDER BY artist_popularity DESC, name
        LIMIT 200
    """)

    st.sidebar.header("Artist Selection")
    selected_name = st.sidebar.selectbox("Search Artist", artists["name"].tolist())
    row = artists[artists["name"] == selected_name].iloc[0]
    aid = row["id"]

    # KPIs via Part 3 get_data
    ts = get_data("SELECT COUNT(*) AS tracks, COUNT(DISTINCT album_id) AS albums "
                  "FROM albums_data WHERE artist_id = ?", (aid,))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Popularity", int(row["artist_popularity"]))
    c2.metric("Followers", fmt(row["followers"]))
    c3.metric("Tracks", int(ts["tracks"][0]))
    c4.metric("Albums", int(ts["albums"][0]))

    gr = get_data("SELECT artist_genres FROM artist_data WHERE id = ?", (aid,))
    st.markdown(f"**Genres:** {gr['artist_genres'][0]}")

    # Part 1 correlation
    df_artists = cached_load_artist_data()
    corr = get_correlation(df_artists)
    st.caption(f"ℹ️ Overall popularity-followers correlation: **{corr:.3f}**")

    col1, col2 = st.columns(2)
    with col1:
        tp = get_data("""
            SELECT t.track_popularity FROM tracks_data t
            JOIN albums_data al ON t.id = al.track_id WHERE al.artist_id = ?
        """, (aid,))
        if not tp.empty:
            fig = px.histogram(tp, x="track_popularity", nbins=30,
                               color_discrete_sequence=[SPOTIFY_GREEN])
            style_fig(fig, "Track Popularity Distribution")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        feat = get_data("""
            SELECT AVG(f.danceability) AS danceability, AVG(f.energy) AS energy,
                   AVG(f.speechiness) AS speechiness, AVG(f.acousticness) AS acousticness,
                   AVG(f.instrumentalness) AS instrumentalness,
                   AVG(f.liveness) AS liveness, AVG(f.valence) AS valence
            FROM features_data f JOIN albums_data al ON f.id = al.track_id
            WHERE al.artist_id = ?
        """, (aid,))
        if not feat.empty:
            vals = [feat[c][0] if feat[c][0] is not None else 0 for c in AUDIO_FEATURES]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=AUDIO_FEATURES+[AUDIO_FEATURES[0]],
                                          fill="toself", name=selected_name, line_color=SPOTIFY_GREEN))
            style_fig(fig, f"Audio Profile - {selected_name}")
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])))
            st.plotly_chart(fig, use_container_width=True)

    # Album timeline via Part 3 get_data
    timeline = get_data("""
        SELECT al.track_name, al.album_name,
               CAST(SUBSTR(al.release_date,1,4) AS INTEGER) AS year, t.track_popularity
        FROM albums_data al JOIN tracks_data t ON al.track_id = t.id
        WHERE al.artist_id = ? AND CAST(SUBSTR(al.release_date,1,4) AS INTEGER) > 1900
        ORDER BY year
    """, (aid,))
    if not timeline.empty:
        fig = px.scatter(timeline, x="year", y="track_popularity",
                         color="album_name", hover_name="track_name",
                         color_discrete_sequence=PALETTE)
        style_fig(fig, "Track Timeline by Album", height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 Tracks")
    top_tracks = get_data("""
        SELECT al.track_name, t.track_popularity, al.album_name
        FROM albums_data al JOIN tracks_data t ON al.track_id = t.id
        WHERE al.artist_id = ? ORDER BY t.track_popularity DESC LIMIT 10
    """, (aid,))
    if not top_tracks.empty:
        st.dataframe(top_tracks, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 4: TIME ANALYSIS
# Uses: Part 3 (get_data, analyze_collaborations, analyze_explicit_tracks)
#       Part 4 (assign_era, add_era_column, get_era_features,
#               get_feature_trends, get_yearly_popularity)
# Requirement: time component with year filtering
# ══════════════════════════════════════════════════════════════════
def page_time_analysis():
    st.title("⏳ Music Through Time")

    st.sidebar.header("Time Filters")
    year_range = st.sidebar.slider("Year Range", 1960, 2023, (1960, 2023))
    group_by = st.sidebar.radio("Group By", ["Year", "Decade"])
    time_features = st.sidebar.multiselect(
        "Features to Plot", AUDIO_FEATURES,
        default=["danceability", "energy", "valence"])

    year_col = "CAST(SUBSTR(al.release_date,1,4) AS INTEGER)"
    time_col = f"({year_col}/10*10)" if group_by == "Decade" else year_col
    label = "decade" if group_by == "Decade" else "year"

    # Feature trends via Part 3 get_data
    if time_features:
        st.subheader("Audio Feature Trends")
        aggs = ", ".join([f"AVG(f.{ft}) AS {ft}" for ft in time_features])
        trends = get_data(f"""
            SELECT {time_col} AS {label}, {aggs}
            FROM features_data f JOIN albums_data al ON f.id = al.track_id
            WHERE {year_col} BETWEEN ? AND ?
            GROUP BY {label} HAVING COUNT(*) >= 10 ORDER BY {label}
        """, (year_range[0], year_range[1]))
        if not trends.empty:
            melted = trends.melt(id_vars=[label], var_name="feature", value_name="value")
            fig = px.line(melted, x=label, y="value", color="feature",
                          color_discrete_sequence=PALETTE, markers=True)
            style_fig(fig, f"Feature Trends by {group_by}")
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    # Explicit trend - same query pattern as Part 3 task_explicit_collabs.py
    with col1:
        ex = get_data(f"""
            SELECT {time_col} AS {label},
                   ROUND(100.0 * SUM(CASE WHEN t.explicit='true' THEN 1 ELSE 0 END)
                         / COUNT(*), 1) AS explicit_pct
            FROM tracks_data t JOIN albums_data al ON t.id = al.track_id
            WHERE {year_col} BETWEEN ? AND ?
            GROUP BY {label} HAVING COUNT(*) >= 10 ORDER BY {label}
        """, (year_range[0], year_range[1]))
        if not ex.empty:
            fig = px.area(ex, x=label, y="explicit_pct",
                          color_discrete_sequence=[SPOTIFY_GREEN], line_shape="linear")
            style_fig(fig, "Explicit Content Over Time")
            st.plotly_chart(fig, use_container_width=True)

    # Collaboration rate - same query pattern as Part 3 collaborations.py
    with col2:
        co = get_data(f"""
            SELECT {time_col} AS {label},
                   ROUND(100.0 * SUM(CASE WHEN al.artist_1 IS NOT NULL
                         AND al.artist_1 != '' THEN 1 ELSE 0 END)
                         / COUNT(*), 1) AS collab_pct
            FROM albums_data al
            WHERE {year_col} BETWEEN ? AND ?
            GROUP BY {label} HAVING COUNT(*) >= 10 ORDER BY {label}
        """, (year_range[0], year_range[1]))
        if not co.empty:
            fig = px.line(co, x=label, y="collab_pct",
                          color_discrete_sequence=[SPOTIFY_GREEN], markers=True)
            style_fig(fig, "Collaboration Rate Over Time")
            st.plotly_chart(fig, use_container_width=True)

    # Era comparison - uses Part 4 assign_era + get_era_features
    st.subheader("Era Comparison")
    tracks, features, artists, albums = cached_load_all()
    t_clean, f_clean, a_clean = cached_clean_data(tracks, features, albums)
    a_clean = add_era_column(a_clean)       # Part 4
    # Filter to selected year range
    a_filtered = a_clean[(a_clean["year"] >= year_range[0]) & (a_clean["year"] <= year_range[1])]
    era_avg = get_era_features(a_filtered, f_clean)  # Part 4

    if not era_avg.empty:
        era_reset = era_avg.reset_index()
        cols_to_plot = [c for c in ["danceability", "energy", "valence"] if c in era_reset.columns]
        melted = era_reset.melt(id_vars=["era"], value_vars=cols_to_plot,
                                var_name="feature", value_name="avg_value")
        fig = px.bar(melted, x="era", y="avg_value", color="feature",
                     barmode="group", color_discrete_sequence=PALETTE)
        style_fig(fig, "Average Features by Era")
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 5: DEEP DIVE
# Uses: Part 1 (overperformers, regression)
#       Part 3 (analyze_collaborations, analyze_album_consistency)
#       Part 4 (detect_outliers_iqr, album_feature_summary)
# ══════════════════════════════════════════════════════════════════
def page_deep_dive():
    st.title("🔬 Deep Dive Analyses")
    st.sidebar.header("Analysis Selection")
    analysis = st.sidebar.radio("Choose Analysis", [
        "Over-Performers & Legacy",
        "Outlier Detection",
        "Album Feature Summary",
        "Collaboration Analysis",
        "Album Consistency Analysis",
    ])
    if   analysis.startswith("Over"):   _deep_overperformers()
    elif analysis.startswith("Outlier"): _deep_outliers()
    elif analysis.startswith("Album F"): _deep_album_summary()
    elif analysis.startswith("Collab"):  _deep_collaboration()
    else:                                _deep_album_consistency()

# Over-performers & legacy artists 
def _deep_overperformers():
    df = cached_load_artist_data()
    correlation = get_correlation(df)

    st.divider()
    st.subheader("Popularity vs Followers")

    col1, spacer, col2 = st.columns([1, 0.2, 2])

    with col1:
        st.metric(
            "Correlation between popularity and log followers",
            f"{correlation:.3f}"
        )

        st.write("")
        st.write("")

        st.markdown(
            """
            **Insight 💡**  
            There is a strong positive relationship between followers and popularity.  
            However, some artists significantly over- or under-perform relative to their audience size.
            """
        )

    with col2:
        st.pyplot(plot_popularity_vs_followers(df))

    st.divider()

    st.subheader("Over-performers and Legacy Artists")

    over_performers, legacy_artists = get_overperformers_and_legacy(df)

    over_df = over_performers.reset_index(drop=True)
    over_df.index += 1
    over_df.index.name = "#"

# Style the over-performers table
    styled_over = (
        over_df
        [["name", "artist_popularity", "followers"]]
        .rename(columns={
            "artist_popularity": "Popularity",
            "followers": "Followers"
        }) # Format the table with renamed columns and only relevant info
        .style
        .set_properties(**{
            "background-color": "#191414",
            "color": "white",
            "border-color": "#1DB954"
        }) # Set dark background and green borders for the table
        .set_table_styles([
            {"selector": "th", "props": [("background-color", "#1DB954"), ("color", "white")]},
            {"selector": "td", "props": [("border", "1px solid #1DB954")]}
        ]) # Style the header and cells with Spotify green and white text
    )

    # Prepare dataframe first
    legacy_df = legacy_artists.reset_index(drop=True)
    legacy_df.index += 1
    legacy_df.index.name = "#"

    # Style the legacy artists table
    styled_legacy = (
        legacy_df
        [["name", "artist_popularity", "followers"]]
        .rename(columns={
            "artist_popularity": "Popularity",
            "followers": "Followers"
        })
        .style
        .set_properties(**{
            "background-color": "#191414",
            "color": "white",
            "border-color": "#1DB954"
        })
        .set_table_styles([
            {"selector": "th", "props": [("background-color", "#1DB954"), ("color", "white")]},
            {"selector": "td", "props": [("border", "1px solid #1DB954")]}
        ])
    )

    # Display the plot and tables side by side
    left_col, right_col = st.columns([1.8, 1])

    with left_col:
        st.subheader("Model View")
        st.pyplot(plot_overperformers_legacy(df)) # Plot the over-performers and legacy artists in the left column

    with right_col:
        st.subheader("Top 10 Over-performers")

        st.markdown(
            f'<div style="height:200px; overflow-y:auto;">{styled_over.to_html()}</div>',
            unsafe_allow_html=True
        )   # Display the over-performers table in a scrollable div

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        st.subheader("Top 10 Legacy Artists")

        # scrollable table for legacy artists
        st.markdown(
            f'<div style="height:200px; overflow-y:auto;">{styled_legacy.to_html()}</div>',
            unsafe_allow_html=True
        ) 

    st.divider()

        # Add a section for genre breadth analysis
    st.subheader("Genre Breadth Analysis")

    genre_summary = get_num_genres_summary(df)

    col1, col2, col3 = st.columns(3) # Create three columns for the summary metrics

    # Display the summary metrics for number of genres and correlations
    with col1:
        st.metric("Average # of Genres", round(genre_summary["mean_num_genres"], 2))

    with col2:
        st.metric("Correlation with Popularity", round(genre_summary["corr_popularity"], 3))

    with col3:
        st.metric("Correlation with Followers", round(genre_summary["corr_followers"], 3))

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    col4, col5 = st.columns(2)

    # Plot the number of genres vs popularity 
    with col4:
        st.pyplot(plot_num_genres_vs_popularity(df))

    # Plot the number of genres vs followers
    with col5:
        st.pyplot(plot_num_genres_vs_followers(df))

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    st.pyplot(plot_follower_groups_vs_popularity(df))

def _deep_outliers():
    """Directly uses Part 4 detect_outliers_iqr."""
    st.subheader("Outlier Detection (IQR Method)")
    st.markdown("Using `detect_outliers_iqr()` from **Part 4**.")

    feature = st.selectbox("Select Feature", AUDIO_FEATURES_FULL)

    data = get_data(f"""
        SELECT f.[{feature}], al.track_name, al.artist_0
        FROM features_data f JOIN albums_data al ON f.id = al.track_id
        WHERE f.[{feature}] IS NOT NULL
        ORDER BY RANDOM() LIMIT 10000
    """)
    if data.empty:
        return

    outliers, stats = detect_outliers_iqr(data, feature)  # Part 4
    data["is_outlier"] = (data[feature] < stats["lower"]) | (data[feature] > stats["upper"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Q1", f"{stats['Q1']:.3f}")
    c2.metric("Q3", f"{stats['Q3']:.3f}")
    c3.metric("IQR", f"{stats['IQR']:.3f}")
    c4.metric("Outliers", f"{stats['count']} ({100*len(outliers)/len(data):.1f}%)")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.box(data, y=feature, color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, f"{feature.title()} - Box Plot")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.scatter(data, x=data.index, y=feature, color="is_outlier",
                         color_discrete_map={True: ACCENT_CORAL, False: SPOTIFY_GREEN},
                         hover_data=["track_name", "artist_0"], opacity=0.5)
        style_fig(fig, f"{feature.title()} - Outlier Scatter")
        st.plotly_chart(fig, use_container_width=True)

    outlier_rows = data[data["is_outlier"]].nlargest(15, feature)[["track_name", "artist_0", feature]]
    if not outlier_rows.empty:
        st.subheader("Top Outlier Tracks")
        st.dataframe(outlier_rows, use_container_width=True, hide_index=True)


def _deep_album_summary():
    """Directly uses Part 4 album_feature_summary."""
    st.subheader("Album Feature Summary")
    st.markdown("Using `album_feature_summary()` from **Part 4**.")

    albums = get_data("""
        SELECT DISTINCT album_name, album_popularity
        FROM albums_data WHERE album_name IS NOT NULL AND album_name != ''
        ORDER BY album_popularity DESC LIMIT 100
    """)
    selected = st.selectbox("Select Album", albums["album_name"].tolist())

    summary = album_feature_summary(selected)  # Part 4

    if summary is None:
        st.warning("No feature data found for this album.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Energy", f"{summary.get('energy', 0):.3f}")
    c2.metric("Avg Tempo", f"{summary.get('tempo', 0):.1f}")
    c3.metric("Avg Loudness", f"{summary.get('loudness', 0):.1f} dB")

    ov = get_data("""
        SELECT AVG(danceability) AS danceability, AVG(energy) AS energy,
               AVG(speechiness) AS speechiness, AVG(acousticness) AS acousticness,
               AVG(instrumentalness) AS instrumentalness,
               AVG(liveness) AS liveness, AVG(valence) AS valence
        FROM features_data
    """)

    cats = AUDIO_FEATURES
    av = [summary.get(c, 0) for c in cats]
    ov_v = [ov[c][0] for c in cats]

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=av+[av[0]], theta=cats+[cats[0]],
                                      fill="toself", name=selected, line_color=SPOTIFY_GREEN))
        fig.add_trace(go.Scatterpolar(r=ov_v+[ov_v[0]], theta=cats+[cats[0]],
                                      fill="toself", name="Dataset Average",
                                      line_color=ACCENT_BLUE, opacity=0.4))
        style_fig(fig, "Album vs Overall Profile")
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        diff = pd.DataFrame({
            "Feature": cats,
            "Difference": [av[i] - ov_v[i] for i in range(len(cats))],
        })
        fig = px.bar(diff, x="Feature", y="Difference", color="Difference",
                     color_continuous_scale="RdBu", color_continuous_midpoint=0)
        style_fig(fig, "How This Album Differs From Average")
        st.plotly_chart(fig, use_container_width=True)


def _deep_collaboration():
    """Directly uses Part 3 analyze_collaborations."""
    st.subheader("Collaboration Analysis")
    st.markdown("Using `analyze_collaborations()` from **Part 3**.")

    df_collab, avg_popularity, fig_collab = analyze_collaborations()  # Part 3

    c1, c2 = st.columns(2)
    solo = avg_popularity[avg_popularity["Track Type"] == "Solo Track"]
    collab = avg_popularity[avg_popularity["Track Type"] == "Collaboration"]
    c1.metric("Solo Avg Popularity", f"{solo['average_popularity'].values[0]:.1f}")
    c2.metric("Collab Avg Popularity", f"{collab['average_popularity'].values[0]:.1f}")

    col1, col2 = st.columns(2)
    with col1:
        st.pyplot(fig_collab)  # Part 3 matplotlib figure
    with col2:
        fig = px.box(df_collab.sample(min(10000, len(df_collab))),
                     x="is_collab", y="track_popularity",
                     color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, "Popularity by Collaboration Type")
        fig.update_xaxes(title="Is Collaboration (0=Solo, 1=Collab)")
        st.plotly_chart(fig, use_container_width=True)


def _deep_album_consistency():
    """Directly uses Part 3 analyze_album_consistency."""
    st.subheader("Album Feature Consistency")
    st.markdown("Using `analyze_album_consistency()` from **Part 3**.")

    album_name = st.text_input("Enter album name", "The Dark Side Of The Moon")
    if album_name:
        df_album, fig_album = analyze_album_consistency(album_name)  # Part 3
        if df_album.empty:
            st.warning(f"No tracks found for '{album_name}'.")
            return
        
        col1, spacer, col2 = st.columns([1.8, 0.2, 1])

        with col1:
            st.pyplot(fig_album)

        with col2:
            st.dataframe(df_album, use_container_width=True, hide_index=True)
                


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="Spotify Analytics Dashboard",
        page_icon="🎵", layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(DARK_CSS, unsafe_allow_html=True)

    pages = {
        "📊 Overview": page_overview,
        "🔍 Features & Genres": page_feature_genre,
        "🔎 Artist Search": page_artist_search,
        "⏳ Music Through Time": page_time_analysis,
        "🔬 Deep Dive": page_deep_dive,
    }
    st.sidebar.title("🎵 Spotify Analytics")
    selection = st.sidebar.radio("Navigate", list(pages.keys()))
    pages[selection]()


if __name__ == "__main__":
    main()
