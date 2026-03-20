# Spotify Analytics Dashboard

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import pandas as pd
import numpy as np
import os

# constants

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spotify_database.db")

SPOTIFY_GREEN = "#1DB954"
ACCENT_BLUE = "#4A90D9"
ACCENT_CORAL = "#E8555A"
ACCENT_PURPLE = "#9B59B6"
ACCENT_AMBER = "#F39C12"
PALETTE = [SPOTIFY_GREEN, ACCENT_BLUE, ACCENT_CORAL, ACCENT_PURPLE, ACCENT_AMBER,
           "#2ECC71", "#3498DB", "#E74C3C", "#8E44AD", "#F1C40F"]

AUDIO_FEATURES = [
    "danceability", "energy", "speechiness", "acousticness",
    "instrumentalness", "liveness", "valence"
]
AUDIO_FEATURES_FULL = AUDIO_FEATURES + ["loudness", "tempo"]

KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# helper functions

@st.cache_data(ttl=600)
# runs a sql query and returns a dataframe
def run_query(query, params=()):
    # connect to the database
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn, params=params)
    # close connection
    conn.close()
    return df

def style_fig(fig, title="", height=450):
    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        template="plotly_white",
        height=height,
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(size=12),
        colorway=PALETTE,
    )
    return fig

def fmt_number(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


# Page 1: Overview

def page_overview():
    st.title("Spotify Database Overview")
    st.markdown("Key statistics and distributions across the full dataset.")

    # KPI metrics
    stats = run_query("""
        SELECT
            (SELECT COUNT(*) FROM tracks_data) AS total_tracks,
            (SELECT COUNT(*) FROM artist_data) AS total_artists,
            (SELECT COUNT(*) FROM albums_data) AS total_albums,
            (SELECT AVG(track_popularity) FROM tracks_data) AS avg_popularity,
            (SELECT ROUND(100.0 * SUM(CASE WHEN explicit='true' THEN 1 ELSE 0 END) / COUNT(*), 1)
             FROM tracks_data) AS explicit_pct,
            (SELECT MIN(CAST(SUBSTR(release_date,1,4) AS INTEGER))
             FROM albums_data WHERE CAST(SUBSTR(release_date,1,4) AS INTEGER) > 1900) AS min_year,
            (SELECT MAX(CAST(SUBSTR(release_date,1,4) AS INTEGER)) FROM albums_data) AS max_year
    """)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Tracks", fmt_number(stats["total_tracks"][0]))
    c2.metric("Artists", fmt_number(stats["total_artists"][0]))
    c3.metric("Albums", fmt_number(stats["total_albums"][0]))
    c4.metric("Avg Popularity", f"{stats['avg_popularity'][0]:.1f}")
    c5.metric("Explicit %", f"{stats['explicit_pct'][0]}%")
    c6.metric("Year Range", f"{int(stats['min_year'][0])}-{int(stats['max_year'][0])}")

    col_left, col_right = st.columns(2)

    # Track popularity distribution
    with col_left:
        df = run_query("SELECT track_popularity FROM tracks_data")
        # print(df.head())
        fig = px.histogram(df, x="track_popularity", nbins=50,
                           color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, "Track Popularity Distribution")
        fig.update_xaxes(title="Popularity")
        fig.update_yaxes(title="Count")
        st.plotly_chart(fig, use_container_width=True)

    # Tracks by decade
    with col_right:
        decades = run_query("""
            SELECT (CAST(SUBSTR(release_date,1,4) AS INTEGER)/10*10) AS decade,
                   COUNT(*) AS cnt
            FROM albums_data
            WHERE CAST(SUBSTR(release_date,1,4) AS INTEGER) >= 1950
            GROUP BY decade ORDER BY decade
        """)
        # create the chart
        fig = px.bar(decades, x="decade", y="cnt",
                     color_discrete_sequence=[ACCENT_BLUE])
        style_fig(fig, "Tracks by Decade")
        fig.update_xaxes(title="Decade")
        fig.update_yaxes(title="Number of Tracks")
        st.plotly_chart(fig, use_container_width=True)

    col_left2, col_right2 = st.columns(2)

    # Top 10 labels
    with col_left2:
        labels = run_query("""
            SELECT label, COUNT(*) AS cnt FROM albums_data
            WHERE label IS NOT NULL AND label != ''
            GROUP BY label ORDER BY cnt DESC LIMIT 10
        """)
        fig = px.bar(labels, x="cnt", y="label", orientation="h",
                     color_discrete_sequence=[ACCENT_CORAL])
        style_fig(fig, "Top 10 Record Labels")
        fig.update_yaxes(autorange="reversed", title="")
        fig.update_xaxes(title="Number of Tracks")
        st.plotly_chart(fig, use_container_width=True)

    # Album type distribution
    with col_right2:
        types = run_query("""
            SELECT album_type, COUNT(*) AS cnt FROM albums_data
            GROUP BY album_type ORDER BY cnt DESC
        """)
        fig = px.pie(types, values="cnt", names="album_type",
                     color_discrete_sequence=PALETTE)
        style_fig(fig, "Album Type Distribution")
        # show the chart
        st.plotly_chart(fig, use_container_width=True)


# Page 2: Genre Explorer

def page_genre_explorer():
    st.title("Genre Explorer")

    # Load top genres
    genres = run_query("""
        SELECT genre, COUNT(*) AS cnt FROM (
            SELECT genre_0 AS genre FROM artist_data WHERE genre_0 != '' AND genre_0 IS NOT NULL
            UNION ALL
            SELECT genre_1 FROM artist_data WHERE genre_1 != '' AND genre_1 IS NOT NULL
            UNION ALL
            SELECT genre_2 FROM artist_data WHERE genre_2 != '' AND genre_2 IS NOT NULL
            UNION ALL
            SELECT genre_3 FROM artist_data WHERE genre_3 != '' AND genre_3 IS NOT NULL
            UNION ALL
            SELECT genre_4 FROM artist_data WHERE genre_4 != '' AND genre_4 IS NOT NULL
        ) GROUP BY genre ORDER BY cnt DESC LIMIT 50
    """)
    genre_list = genres["genre"].tolist()

    st.sidebar.header("Genre Filters")
    # TODO: maybe add more genres or allow multi-select later
    selected_genre = st.sidebar.selectbox("Select Genre", genre_list)
    min_pop = st.sidebar.slider("Min Artist Popularity", 0, 100, 0)

    # Top 15 artists in genre
    top_artists = run_query("""
        SELECT a.name, a.artist_popularity, a.followers
        FROM artist_data a
        WHERE a.artist_popularity >= ?
          AND (a.genre_0 = ? OR a.genre_1 = ? OR a.genre_2 = ? OR a.genre_3 = ? OR a.genre_4 = ?)
        ORDER BY a.artist_popularity DESC LIMIT 15
    """, (min_pop, selected_genre, selected_genre, selected_genre, selected_genre, selected_genre))

    if top_artists.empty:
        st.warning("No artists found for this genre/popularity combination.")
        return

    col_l, col_r = st.columns(2)
    with col_l:
        fig = px.bar(top_artists, x="artist_popularity", y="name", orientation="h",
                     color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, f"Top 15 Artists — {selected_genre}")
        fig.update_yaxes(autorange="reversed", title="")
        fig.update_xaxes(title="Popularity")
        st.plotly_chart(fig, use_container_width=True)

    # Popularity vs Followers scatter
    with col_r:
        scatter_data = run_query("""
            SELECT a.name, a.artist_popularity, a.followers
            FROM artist_data a
            WHERE a.artist_popularity >= ?
              AND a.followers > 0
              AND (a.genre_0 = ? OR a.genre_1 = ? OR a.genre_2 = ? OR a.genre_3 = ? OR a.genre_4 = ?)
        """, (min_pop, selected_genre, selected_genre, selected_genre, selected_genre, selected_genre))

        if not scatter_data.empty:
            fig = px.scatter(scatter_data, x="followers", y="artist_popularity",
                             hover_name="name", log_x=True,
                             color_discrete_sequence=[ACCENT_BLUE])
            style_fig(fig, "Popularity vs Followers (log scale)")
            fig.update_xaxes(title="Followers (log)")
            fig.update_yaxes(title="Popularity")
            x_log = np.log10(scatter_data["followers"].replace(0, np.nan).dropna())
            y_vals = scatter_data.loc[x_log.index, "artist_popularity"]
            coeffs = np.polyfit(x_log, y_vals, 1)
            x_fit = np.linspace(x_log.min(), x_log.max(), 100)
            y_fit = np.polyval(coeffs, x_fit)
            fig.add_trace(go.Scatter(x=10**x_fit, y=y_fit, mode="lines",
                                     line=dict(color="white", dash="dash"), name="Trend"))
            st.plotly_chart(fig, use_container_width=True)

    # Feature radar for genre
    genre_features = run_query("""
        SELECT AVG(f.danceability) AS danceability, AVG(f.energy) AS energy,
               AVG(f.speechiness) AS speechiness, AVG(f.acousticness) AS acousticness,
               AVG(f.instrumentalness) AS instrumentalness, AVG(f.liveness) AS liveness,
               AVG(f.valence) AS valence
        FROM features_data f
        JOIN albums_data al ON f.id = al.track_id
        JOIN artist_data a ON al.artist_id = a.id
        WHERE (a.genre_0 = ? OR a.genre_1 = ? OR a.genre_2 = ? OR a.genre_3 = ? OR a.genre_4 = ?)
    """, (selected_genre, selected_genre, selected_genre, selected_genre, selected_genre))

    overall_features = run_query("""
        SELECT AVG(danceability) AS danceability, AVG(energy) AS energy,
               AVG(speechiness) AS speechiness, AVG(acousticness) AS acousticness,
               AVG(instrumentalness) AS instrumentalness, AVG(liveness) AS liveness,
               AVG(valence) AS valence
        FROM features_data
    """)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        cats = AUDIO_FEATURES
        genre_vals = [genre_features[c][0] for c in cats]
        overall_vals = [overall_features[c][0] for c in cats]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=genre_vals + [genre_vals[0]],
                                       theta=cats + [cats[0]],
                                       fill="toself", name=selected_genre,
                                       line_color=SPOTIFY_GREEN))
        fig.add_trace(go.Scatterpolar(r=overall_vals + [overall_vals[0]],
                                       theta=cats + [cats[0]],
                                       fill="toself", name="Overall",
                                       line_color=ACCENT_BLUE, opacity=0.4))
        style_fig(fig, f"Audio Feature Profile — {selected_genre}")
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])))
        st.plotly_chart(fig, use_container_width=True)

    # Explicit % comparison
    with col_r2:
        explicit_genre = run_query("""
            SELECT
                SUM(CASE WHEN t.explicit='true' THEN 1 ELSE 0 END) AS explicit_cnt,
                COUNT(*) AS total
            FROM tracks_data t
            JOIN albums_data al ON t.id = al.track_id
            JOIN artist_data a ON al.artist_id = a.id
            WHERE (a.genre_0 = ? OR a.genre_1 = ? OR a.genre_2 = ? OR a.genre_3 = ? OR a.genre_4 = ?)
        """, (selected_genre, selected_genre, selected_genre, selected_genre, selected_genre))

        explicit_overall = run_query("""
            SELECT SUM(CASE WHEN explicit='true' THEN 1 ELSE 0 END) AS explicit_cnt,
                   COUNT(*) AS total
            FROM tracks_data
        """)

        genre_pct = 100.0 * explicit_genre["explicit_cnt"][0] / max(explicit_genre["total"][0], 1)
        overall_pct = 100.0 * explicit_overall["explicit_cnt"][0] / max(explicit_overall["total"][0], 1)

        comp_df = pd.DataFrame({
            "Category": [selected_genre, "Overall"],
            "Explicit %": [genre_pct, overall_pct]
        })
        fig = px.bar(comp_df, x="Category", y="Explicit %",
                     color="Category", color_discrete_sequence=[ACCENT_CORAL, ACCENT_BLUE])
        style_fig(fig, "Explicit Content: Genre vs Overall")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Genre popularity box plot (top 10 genres)
    st.subheader("Popularity Distribution Across Top Genres")
    box_data = run_query("""
        SELECT g.genre, a.artist_popularity
        FROM (
            SELECT genre_0 AS genre, id FROM artist_data WHERE genre_0 != '' AND genre_0 IS NOT NULL
        ) g
        JOIN artist_data a ON g.id = a.id
        WHERE g.genre IN (
            SELECT genre_0 FROM artist_data WHERE genre_0 != '' AND genre_0 IS NOT NULL
            GROUP BY genre_0 ORDER BY COUNT(*) DESC LIMIT 10
        )
    """)
    if not box_data.empty:
        fig = px.box(box_data, x="genre", y="artist_popularity",
                     color_discrete_sequence=[ACCENT_PURPLE])
        style_fig(fig, "Artist Popularity by Top 10 Genres", height=400)
        fig.update_xaxes(title="Genre", tickangle=45)
        fig.update_yaxes(title="Artist Popularity")
        st.plotly_chart(fig, use_container_width=True)


# Page 3: Artist Search

def page_artist_search():
    st.title("Artist Search")

    # Load searchable artists (popularity >= 70)
    artists = run_query("""
        SELECT id, name, artist_popularity, followers
        FROM artist_data
        WHERE artist_popularity >= 70
        ORDER BY artist_popularity DESC, name
    """)

    st.sidebar.header("Artist Selection")
    artist_names = artists["name"].tolist()
    selected_name = st.sidebar.selectbox("Search Artist", artist_names)

    artist_row = artists[artists["name"] == selected_name].iloc[0]
    artist_id = artist_row["id"]

    # Header KPIs
    track_stats = run_query("""
        SELECT COUNT(*) AS track_count,
               COUNT(DISTINCT album_id) AS album_count
        FROM albums_data WHERE artist_id = ?
    """, (artist_id,))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Popularity", int(artist_row["artist_popularity"]))
    c2.metric("Followers", fmt_number(artist_row["followers"]))
    c3.metric("Tracks", int(track_stats["track_count"][0]))
    c4.metric("Albums", int(track_stats["album_count"][0]))

    # Genres
    genre_row = run_query("SELECT artist_genres FROM artist_data WHERE id = ?", (artist_id,))
    st.markdown(f"**Genres:** {genre_row['artist_genres'][0]}")

    col_l, col_r = st.columns(2)

    # Track popularity histogram
    with col_l:
        track_pops = run_query("""
            SELECT t.track_popularity
            FROM tracks_data t
            JOIN albums_data al ON t.id = al.track_id
            WHERE al.artist_id = ?
        """, (artist_id,))
        if not track_pops.empty:
            fig = px.histogram(track_pops, x="track_popularity", nbins=30,
                               color_discrete_sequence=[SPOTIFY_GREEN])
            style_fig(fig, "Track Popularity Distribution")
            fig.update_xaxes(title="Popularity")
            fig.update_yaxes(title="Count")
            st.plotly_chart(fig, use_container_width=True)

    # Feature radar
    with col_r:
        feat = run_query("""
            SELECT AVG(f.danceability) AS danceability, AVG(f.energy) AS energy,
                   AVG(f.speechiness) AS speechiness, AVG(f.acousticness) AS acousticness,
                   AVG(f.instrumentalness) AS instrumentalness, AVG(f.liveness) AS liveness,
                   AVG(f.valence) AS valence
            FROM features_data f
            JOIN albums_data al ON f.id = al.track_id
            WHERE al.artist_id = ?
        """, (artist_id,))
        if not feat.empty:
            cats = AUDIO_FEATURES
            vals = [feat[c][0] if feat[c][0] is not None else 0 for c in cats]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=vals + [vals[0]],
                                           theta=cats + [cats[0]],
                                           fill="toself", name=selected_name,
                                           line_color=SPOTIFY_GREEN))
            style_fig(fig, f"Audio Profile — {selected_name}")
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])))
            st.plotly_chart(fig, use_container_width=True)

    # Album timeline
    timeline = run_query("""
        SELECT al.track_name, al.album_name,
               CAST(SUBSTR(al.release_date,1,4) AS INTEGER) AS year,
               t.track_popularity
        FROM albums_data al
        JOIN tracks_data t ON al.track_id = t.id
        WHERE al.artist_id = ?
          AND CAST(SUBSTR(al.release_date,1,4) AS INTEGER) > 1900
        ORDER BY year
    """, (artist_id,))

    if not timeline.empty:
        fig = px.scatter(timeline, x="year", y="track_popularity",
                         color="album_name", hover_name="track_name",
                         color_discrete_sequence=PALETTE)
        style_fig(fig, "Track Timeline by Album", height=400)
        fig.update_xaxes(title="Year")
        fig.update_yaxes(title="Track Popularity")
        st.plotly_chart(fig, use_container_width=True)

    col_l2, col_r2 = st.columns(2)

    # Top 10 tracks
    with col_l2:
        st.subheader("Top 10 Tracks")
        top_tracks = run_query("""
            SELECT al.track_name, t.track_popularity, al.album_name
            FROM albums_data al
            JOIN tracks_data t ON al.track_id = t.id
            WHERE al.artist_id = ?
            ORDER BY t.track_popularity DESC LIMIT 10
        """, (artist_id,))
        if not top_tracks.empty:
            st.dataframe(top_tracks, use_container_width=True, hide_index=True)

    # Explicit/Clean pie + Top collaborators
    with col_r2:
        explicit_data = run_query("""
            SELECT t.explicit, COUNT(*) AS cnt
            FROM tracks_data t
            JOIN albums_data al ON t.id = al.track_id
            WHERE al.artist_id = ?
            GROUP BY t.explicit
        """, (artist_id,))
        if not explicit_data.empty:
            explicit_data["label"] = explicit_data["explicit"].map(
                {"true": "Explicit", "false": "Clean"})
            fig = px.pie(explicit_data, values="cnt", names="label",
                         color_discrete_sequence=[ACCENT_CORAL, SPOTIFY_GREEN])
            style_fig(fig, "Explicit vs Clean", height=300)
            st.plotly_chart(fig, use_container_width=True)

        collabs = run_query("""
            SELECT artist_1 AS collaborator, COUNT(*) AS cnt
            FROM albums_data
            WHERE artist_id = ? AND artist_1 IS NOT NULL AND artist_1 != ''
            GROUP BY artist_1 ORDER BY cnt DESC LIMIT 5
        """, (artist_id,))
        if not collabs.empty:
            st.subheader("Top Collaborators")
            st.dataframe(collabs, use_container_width=True, hide_index=True)


# Page 4: Track Features

def page_track_features():
    st.title("Track Audio Features")

    st.sidebar.header("Feature Filters")
    selected_features = st.sidebar.multiselect("Select Features", AUDIO_FEATURES_FULL,
                                                default=["danceability", "energy", "valence"])
    color_by = st.sidebar.selectbox("Color By", ["explicit", "album_type", "mode", "key"])
    pop_range = st.sidebar.slider("Popularity Range", 0, 100, (0, 100))

    if not selected_features:
        st.info("Select at least one feature from the sidebar.")
        return

    # TODO: could add more filtering options here
    # Correlation heatmap
    st.subheader("Feature Correlation Matrix")
    corr_data = run_query(f"""
        SELECT {', '.join(AUDIO_FEATURES_FULL)}
        FROM features_data
        ORDER BY RANDOM() LIMIT 10000
    """)
    corr_matrix = corr_data.corr()
    fig = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, aspect="auto")
    style_fig(fig, "Feature Correlation Heatmap", height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Feature distributions (violin)
    st.subheader("Feature Distributions")
    dist_data = run_query(f"""
        SELECT {', '.join(selected_features)}
        FROM features_data
        ORDER BY RANDOM() LIMIT 5000
    """)
    melted = dist_data.melt(var_name="feature", value_name="value")
    fig = px.violin(melted, x="feature", y="value", color="feature",
                    color_discrete_sequence=PALETTE, box=True)
    style_fig(fig, "Feature Value Distributions")
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Value")
    st.plotly_chart(fig, use_container_width=True)

    # Feature vs popularity scatter
    if len(selected_features) >= 1:
        st.subheader("Feature vs Popularity")
        feat_choice = st.selectbox("Feature for scatter", selected_features)

        color_col_map = {
            "explicit": "t.explicit",
            "album_type": "al.album_type",
            "mode": "f.mode",
            "key": "f.key",
        }
        color_sql = color_col_map[color_by]

        scatter = run_query(f"""
            SELECT f.{feat_choice}, t.track_popularity, {color_sql} AS color_val
            FROM features_data f
            JOIN tracks_data t ON f.id = t.id
            JOIN albums_data al ON f.id = al.track_id
            WHERE t.track_popularity BETWEEN ? AND ?
            ORDER BY RANDOM() LIMIT 5000
        """, (pop_range[0], pop_range[1]))

        if not scatter.empty:
            if color_by == "key":
                scatter["color_val"] = scatter["color_val"].apply(
                    lambda k: KEY_NAMES[int(k)] if pd.notna(k) and 0 <= int(k) <= 11 else "Unknown")
            elif color_by == "mode":
                scatter["color_val"] = scatter["color_val"].map({0: "Minor", 1: "Major"})

            fig = px.scatter(scatter, x=feat_choice, y="track_popularity",
                             color="color_val",
                             color_discrete_sequence=PALETTE, opacity=0.5)
            style_fig(fig, f"{feat_choice.title()} vs Track Popularity")
            fig.update_xaxes(title=feat_choice.title())
            fig.update_yaxes(title="Track Popularity")
            valid = scatter[[feat_choice, "track_popularity"]].dropna()
            coeffs = np.polyfit(valid[feat_choice], valid["track_popularity"], 1)
            x_fit = np.linspace(valid[feat_choice].min(), valid[feat_choice].max(), 100)
            y_fit = np.polyval(coeffs, x_fit)
            fig.add_trace(go.Scatter(x=x_fit, y=y_fit, mode="lines",
                                     line=dict(color="white", dash="dash"), name="Trend"))
            st.plotly_chart(fig, use_container_width=True)

    # Key distribution by mode
    st.subheader("Key Distribution by Mode")
    key_data = run_query("""
        SELECT key, mode, COUNT(*) AS cnt
        FROM features_data
        WHERE key >= 0 AND key <= 11
        GROUP BY key, mode
    """)
    key_data["key_name"] = key_data["key"].apply(lambda k: KEY_NAMES[k])
    key_data["mode_name"] = key_data["mode"].map({0: "Minor", 1: "Major"})
    fig = px.bar(key_data, x="key_name", y="cnt", color="mode_name",
                 barmode="group", color_discrete_sequence=[ACCENT_BLUE, ACCENT_CORAL])
    style_fig(fig, "Musical Key Distribution")
    fig.update_xaxes(title="Key")
    fig.update_yaxes(title="Count")
    st.plotly_chart(fig, use_container_width=True)


# Page 5: Music Through Time

def page_through_time():
    st.title("Music Through Time")

    st.sidebar.header("Time Filters")
    year_range = st.sidebar.slider("Year Range", 1960, 2023, (1960, 2023))
    group_by = st.sidebar.radio("Group By", ["Year", "Decade"])
    time_features = st.sidebar.multiselect("Features to Plot",
                                            AUDIO_FEATURES,
                                            default=["danceability", "energy", "valence"])

    year_col = "CAST(SUBSTR(al.release_date,1,4) AS INTEGER)"
    if group_by == "Decade":
        time_col = f"({year_col}/10*10)"
        time_label = "decade"
    else:
        time_col = year_col
        time_label = "year"

    # Feature trends over time
    if time_features:
        st.subheader("Audio Feature Trends")
        feat_aggs = ", ".join([f"AVG(f.{feat}) AS {feat}" for feat in time_features])
        trends = run_query(f"""
            SELECT {time_col} AS {time_label}, {feat_aggs}
            FROM features_data f
            JOIN albums_data al ON f.id = al.track_id
            WHERE {year_col} BETWEEN ? AND ?
            GROUP BY {time_label}
            HAVING COUNT(*) >= 10
            ORDER BY {time_label}
        """, (year_range[0], year_range[1]))

        if not trends.empty:
            melted = trends.melt(id_vars=[time_label], var_name="feature", value_name="value")
            fig = px.line(melted, x=time_label, y="value", color="feature",
                          color_discrete_sequence=PALETTE, markers=True)
            style_fig(fig, f"Feature Trends by {group_by}")
            fig.update_xaxes(title=group_by)
            fig.update_yaxes(title="Average Value")
            st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns(2)

    # Explicit content trend
    with col_l:
        explicit_trend = run_query(f"""
            SELECT {time_col} AS {time_label},
                   ROUND(100.0 * SUM(CASE WHEN t.explicit='true' THEN 1 ELSE 0 END) / COUNT(*), 1) AS explicit_pct
            FROM tracks_data t
            JOIN albums_data al ON t.id = al.track_id
            WHERE {year_col} BETWEEN ? AND ?
            GROUP BY {time_label}
            HAVING COUNT(*) >= 10
            ORDER BY {time_label}
        """, (year_range[0], year_range[1]))

        if not explicit_trend.empty:
            fig = px.area(explicit_trend, x=time_label, y="explicit_pct",
                          color_discrete_sequence=[ACCENT_CORAL])
            style_fig(fig, "Explicit Content Over Time")
            fig.update_xaxes(title=group_by)
            fig.update_yaxes(title="Explicit %")
            st.plotly_chart(fig, use_container_width=True)

    # Average track duration
    with col_r:
        dur_trend = run_query(f"""
            SELECT {time_col} AS {time_label},
                   AVG(al.duration_sec) AS avg_duration
            FROM albums_data al
            WHERE {year_col} BETWEEN ? AND ?
              AND al.duration_sec > 0
            GROUP BY {time_label}
            HAVING COUNT(*) >= 10
            ORDER BY {time_label}
        """, (year_range[0], year_range[1]))

        if not dur_trend.empty:
            fig = px.line(dur_trend, x=time_label, y="avg_duration",
                          color_discrete_sequence=[ACCENT_PURPLE], markers=True)
            style_fig(fig, "Average Track Duration")
            fig.update_xaxes(title=group_by)
            fig.update_yaxes(title="Duration (seconds)")
            st.plotly_chart(fig, use_container_width=True)

    col_l2, col_r2 = st.columns(2)

    # Loudness war
    with col_l2:
        loud_trend = run_query(f"""
            SELECT {time_col} AS {time_label},
                   AVG(f.loudness) AS avg_loudness
            FROM features_data f
            JOIN albums_data al ON f.id = al.track_id
            WHERE {year_col} BETWEEN ? AND ?
            GROUP BY {time_label}
            HAVING COUNT(*) >= 10
            ORDER BY {time_label}
        """, (year_range[0], year_range[1]))

        if not loud_trend.empty:
            fig = px.line(loud_trend, x=time_label, y="avg_loudness",
                          color_discrete_sequence=[ACCENT_AMBER], markers=True)
            style_fig(fig, "The Loudness War")
            fig.update_xaxes(title=group_by)
            fig.update_yaxes(title="Average Loudness (dB)")
            st.plotly_chart(fig, use_container_width=True)

    # Collaboration rate
    with col_r2:
        collab_trend = run_query(f"""
            SELECT {time_col} AS {time_label},
                   ROUND(100.0 * SUM(CASE WHEN al.artist_1 IS NOT NULL AND al.artist_1 != '' THEN 1 ELSE 0 END) / COUNT(*), 1) AS collab_pct
            FROM albums_data al
            WHERE {year_col} BETWEEN ? AND ?
            GROUP BY {time_label}
            HAVING COUNT(*) >= 10
            ORDER BY {time_label}
        """, (year_range[0], year_range[1]))

        if not collab_trend.empty:
            fig = px.line(collab_trend, x=time_label, y="collab_pct",
                          color_discrete_sequence=[SPOTIFY_GREEN], markers=True)
            style_fig(fig, "Collaboration Rate Over Time")
            fig.update_xaxes(title=group_by)
            fig.update_yaxes(title="% Tracks with Collaborators")
            st.plotly_chart(fig, use_container_width=True)

    # Album type over time
    st.subheader("Album Types Over Time")
    album_type_trend = run_query(f"""
        SELECT {time_col} AS {time_label}, album_type, COUNT(*) AS cnt
        FROM albums_data al
        WHERE {year_col} BETWEEN ? AND ?
          AND album_type IS NOT NULL
        GROUP BY {time_label}, album_type
        ORDER BY {time_label}
    """, (year_range[0], year_range[1]))

    if not album_type_trend.empty:
        fig = px.bar(album_type_trend, x=time_label, y="cnt", color="album_type",
                     color_discrete_sequence=PALETTE)
        style_fig(fig, "Album Types Over Time")
        fig.update_xaxes(title=group_by)
        fig.update_yaxes(title="Count")
        st.plotly_chart(fig, use_container_width=True)


# Page 6: Deep Dive (Bonus)

def page_deep_dive():
    st.title("Deep Dive Analyses")

    st.sidebar.header("Analysis Selection")
    analysis = st.sidebar.radio("Choose Analysis", [
        "Popularity vs Followers Regression",
        "Collaboration Analysis",
        "Outlier Detection",
        "Album Feature Summary"
    ])

    if analysis == "Popularity vs Followers Regression":
        _deep_regression()
    elif analysis == "Collaboration Analysis":
        _deep_collaboration()
    elif analysis == "Outlier Detection":
        _deep_outliers()
    else:
        _deep_album_summary()


def _deep_regression():
    st.subheader("Popularity vs Followers — Log Regression")
    st.markdown("Exploring the relationship between artist followers and popularity using logarithmic regression.")

    data = run_query("""
        SELECT name, artist_popularity, followers
        FROM artist_data
        WHERE followers > 0 AND artist_popularity > 0
    """)

    if data.empty:
        return

    data["log_followers"] = np.log10(data["followers"].astype(float))

    # Fit log regression
    from scipy import stats as sp_stats
    slope, intercept, r_value, p_value, std_err = sp_stats.linregress(
        data["log_followers"], data["artist_popularity"])
    data["predicted"] = slope * data["log_followers"] + intercept
    data["residual"] = data["artist_popularity"] - data["predicted"]

    c1, c2, c3 = st.columns(3)
    c1.metric("R-squared", f"{r_value**2:.4f}")
    c2.metric("Slope", f"{slope:.2f}")
    c3.metric("P-value", f"{p_value:.2e}")

    # Scatter with regression line
    fig = px.scatter(data, x="log_followers", y="artist_popularity",
                     hover_name="name", opacity=0.3,
                     color_discrete_sequence=[ACCENT_BLUE])
    x_range = np.linspace(data["log_followers"].min(), data["log_followers"].max(), 100)
    fig.add_trace(go.Scatter(x=x_range, y=slope * x_range + intercept,
                              mode="lines", name="Regression Line",
                              line=dict(color=ACCENT_CORAL, width=3)))
    style_fig(fig, "Log(Followers) vs Popularity", height=500)
    fig.update_xaxes(title="Log₁₀(Followers)")
    fig.update_yaxes(title="Artist Popularity")
    st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        # Residual distribution
        fig = px.histogram(data, x="residual", nbins=50,
                           color_discrete_sequence=[ACCENT_PURPLE])
        style_fig(fig, "Residual Distribution")
        fig.update_xaxes(title="Residual (Actual - Predicted)")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        # Top over-performers
        st.subheader("Top Over-Performers")
        st.markdown("Artists more popular than their followers predict:")
        over = data.nlargest(10, "residual")[["name", "artist_popularity", "followers", "residual"]]
        over["residual"] = over["residual"].round(1)
        st.dataframe(over, use_container_width=True, hide_index=True)

        st.subheader("Legacy Artists (Under-Performers)")
        st.markdown("Artists with high followers but lower current popularity:")
        under = data.nsmallest(10, "residual")[["name", "artist_popularity", "followers", "residual"]]
        under["residual"] = under["residual"].round(1)
        st.dataframe(under, use_container_width=True, hide_index=True)


def _deep_collaboration():
    st.subheader("Collaboration Analysis")

    collab_stats = run_query("""
        SELECT
            COUNT(*) AS total_tracks,
            SUM(CASE WHEN artist_1 IS NOT NULL AND artist_1 != '' THEN 1 ELSE 0 END) AS collab_tracks,
            SUM(CASE WHEN artist_2 IS NOT NULL AND artist_2 != '' THEN 1 ELSE 0 END) AS three_plus
        FROM albums_data
    """)

    total = collab_stats["total_tracks"][0]
    collabs = collab_stats["collab_tracks"][0]
    three_p = collab_stats["three_plus"][0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Tracks", fmt_number(total))
    c2.metric("Collaboration Tracks", fmt_number(collabs))
    c3.metric("3+ Artists", fmt_number(three_p))

    col_l, col_r = st.columns(2)

    # Number of collaborators distribution
    with col_l:
        collab_counts = run_query("""
            SELECT
                CASE
                    WHEN artist_1 IS NULL OR artist_1 = '' THEN 1
                    WHEN artist_2 IS NULL OR artist_2 = '' THEN 2
                    WHEN artist_3 IS NULL OR artist_3 = '' THEN 3
                    WHEN artist_4 IS NULL OR artist_4 = '' THEN 4
                    ELSE 5
                END AS num_artists,
                COUNT(*) AS cnt
            FROM albums_data
            GROUP BY num_artists
        """)
        fig = px.bar(collab_counts, x="num_artists", y="cnt",
                     color_discrete_sequence=[SPOTIFY_GREEN])
        style_fig(fig, "Distribution of Artist Count per Track")
        fig.update_xaxes(title="Number of Artists", dtick=1)
        fig.update_yaxes(title="Track Count")
        st.plotly_chart(fig, use_container_width=True)

    # Popularity by number of collaborators
    with col_r:
        pop_by_collab = run_query("""
            SELECT
                CASE
                    WHEN al.artist_1 IS NULL OR al.artist_1 = '' THEN 'Solo'
                    WHEN al.artist_2 IS NULL OR al.artist_2 = '' THEN '2 artists'
                    WHEN al.artist_3 IS NULL OR al.artist_3 = '' THEN '3 artists'
                    ELSE '4+ artists'
                END AS collab_type,
                t.track_popularity
            FROM albums_data al
            JOIN tracks_data t ON al.track_id = t.id
            ORDER BY RANDOM() LIMIT 10000
        """)
        if not pop_by_collab.empty:
            fig = px.box(pop_by_collab, x="collab_type", y="track_popularity",
                         color_discrete_sequence=[ACCENT_BLUE])
            style_fig(fig, "Track Popularity by Number of Artists")
            fig.update_xaxes(title="")
            fig.update_yaxes(title="Track Popularity")
            st.plotly_chart(fig, use_container_width=True)

    # Top 15 most collaborative artists
    st.subheader("Top 15 Most Collaborative Artists")
    top_collab = run_query("""
        SELECT a.name, COUNT(*) AS collab_count, a.artist_popularity
        FROM artist_data a
        JOIN albums_data al ON a.id = al.artist_id
        WHERE al.artist_1 IS NOT NULL AND al.artist_1 != ''
        GROUP BY a.id, a.name
        ORDER BY collab_count DESC LIMIT 15
    """)
    if not top_collab.empty:
        fig = px.bar(top_collab, x="collab_count", y="name", orientation="h",
                     color="artist_popularity", color_continuous_scale="Greens")
        style_fig(fig, "Most Collaborative Artists")
        fig.update_yaxes(autorange="reversed", title="")
        fig.update_xaxes(title="Number of Collaboration Tracks")
        st.plotly_chart(fig, use_container_width=True)


def _deep_outliers():
    st.subheader("Outlier Detection (IQR Method)")

    feature = st.selectbox("Select Feature", AUDIO_FEATURES_FULL)

    data = run_query(f"""
        SELECT f.{feature}, f.id, al.track_name, al.artist_0
        FROM features_data f
        JOIN albums_data al ON f.id = al.track_id
        WHERE f.{feature} IS NOT NULL
        ORDER BY RANDOM() LIMIT 10000
    """)

    if data.empty:
        return

    q1 = data[feature].quantile(0.25)
    q3 = data[feature].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    data["is_outlier"] = (data[feature] < lower) | (data[feature] > upper)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Q1", f"{q1:.3f}")
    c2.metric("Q3", f"{q3:.3f}")
    c3.metric("IQR", f"{iqr:.3f}")
    c4.metric("Outliers", f"{data['is_outlier'].sum()} ({100*data['is_outlier'].mean():.1f}%)")

    col_l, col_r = st.columns(2)

    with col_l:
        fig = px.box(data, y=feature, color_discrete_sequence=[ACCENT_BLUE])
        style_fig(fig, f"{feature.title()} — Box Plot")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig = px.scatter(data, x=data.index, y=feature,
                         color="is_outlier",
                         color_discrete_map={True: ACCENT_CORAL, False: ACCENT_BLUE},
                         hover_data=["track_name", "artist_0"], opacity=0.5)
        style_fig(fig, f"{feature.title()} — Outlier Scatter")
        fig.update_xaxes(title="Sample Index")
        fig.update_yaxes(title=feature.title())
        st.plotly_chart(fig, use_container_width=True)

    # Outlier table
    outliers = data[data["is_outlier"]].nlargest(15, feature)[["track_name", "artist_0", feature]]
    if not outliers.empty:
        st.subheader("Top Outlier Tracks")
        st.dataframe(outliers, use_container_width=True, hide_index=True)


def _deep_album_summary():
    st.subheader("Album Feature Summary")

    # Top 100 albums by popularity
    albums = run_query("""
        SELECT DISTINCT album_name, album_id, album_popularity
        FROM albums_data
        WHERE album_name IS NOT NULL AND album_name != ''
        ORDER BY album_popularity DESC LIMIT 100
    """)

    selected_album = st.selectbox("Select Album", albums["album_name"].tolist())
    album_id = albums[albums["album_name"] == selected_album]["album_id"].iloc[0]

    # Album features
    album_feat = run_query("""
        SELECT AVG(f.danceability) AS danceability, AVG(f.energy) AS energy,
               AVG(f.speechiness) AS speechiness, AVG(f.acousticness) AS acousticness,
               AVG(f.instrumentalness) AS instrumentalness, AVG(f.liveness) AS liveness,
               AVG(f.valence) AS valence, AVG(f.tempo) AS tempo, AVG(f.loudness) AS loudness,
               COUNT(*) AS track_count
        FROM features_data f
        JOIN albums_data al ON f.id = al.track_id
        WHERE al.album_id = ?
    """, (album_id,))

    overall = run_query("""
        SELECT AVG(danceability) AS danceability, AVG(energy) AS energy,
               AVG(speechiness) AS speechiness, AVG(acousticness) AS acousticness,
               AVG(instrumentalness) AS instrumentalness, AVG(liveness) AS liveness,
               AVG(valence) AS valence
        FROM features_data
    """)

    c1, c2, c3 = st.columns(3)
    c1.metric("Tracks", int(album_feat["track_count"][0]))
    c2.metric("Avg Tempo", f"{album_feat['tempo'][0]:.1f}")
    c3.metric("Avg Loudness", f"{album_feat['loudness'][0]:.1f} dB")

    col_l, col_r = st.columns(2)

    # Radar: album vs overall
    with col_l:
        cats = AUDIO_FEATURES
        album_vals = [album_feat[c][0] if album_feat[c][0] is not None else 0 for c in cats]
        overall_vals = [overall[c][0] for c in cats]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=album_vals + [album_vals[0]],
                                       theta=cats + [cats[0]],
                                       fill="toself", name=selected_album,
                                       line_color=SPOTIFY_GREEN))
        fig.add_trace(go.Scatterpolar(r=overall_vals + [overall_vals[0]],
                                       theta=cats + [cats[0]],
                                       fill="toself", name="Dataset Average",
                                       line_color=ACCENT_BLUE, opacity=0.4))
        style_fig(fig, "Album vs Overall Feature Profile")
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])))
        st.plotly_chart(fig, use_container_width=True)

    # Track-level table
    with col_r:
        track_details = run_query("""
            SELECT al.track_name, al.track_number,
                   f.danceability, f.energy, f.valence, f.tempo,
                   t.track_popularity
            FROM albums_data al
            JOIN features_data f ON al.track_id = f.id
            JOIN tracks_data t ON al.track_id = t.id
            WHERE al.album_id = ?
            ORDER BY al.track_number
        """, (album_id,))
        if not track_details.empty:
            st.subheader("Track Details")
            st.dataframe(track_details.round(3), use_container_width=True, hide_index=True)

    # Comparison vs dataset averages
    st.subheader("Album vs Dataset Averages")
    comparison = pd.DataFrame({
        "Feature": AUDIO_FEATURES,
        "Album Avg": [album_feat[c][0] if album_feat[c][0] is not None else 0 for c in AUDIO_FEATURES],
        "Dataset Avg": [overall[c][0] for c in AUDIO_FEATURES]
    })
    comparison["Difference"] = comparison["Album Avg"] - comparison["Dataset Avg"]
    comparison = comparison.round(4)

    fig = px.bar(comparison, x="Feature", y="Difference",
                 color="Difference", color_continuous_scale="RdBu",
                 color_continuous_midpoint=0)
    style_fig(fig, "How This Album Differs From Average")
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Difference from Dataset Mean")
    st.plotly_chart(fig, use_container_width=True)


# main

def main():
    st.set_page_config(
        page_title="Spotify Analytics Dashboard",
        page_icon="🎵",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # TODO: could add more pages in the future
    pages = {
        "Overview": page_overview,
        "Genre Explorer": page_genre_explorer,
        "Artist Search": page_artist_search,
        "Track Features": page_track_features,
        "Music Through Time": page_through_time,
        "Deep Dive": page_deep_dive,
    }

    st.sidebar.title("Spotify Analytics")
    selection = st.sidebar.radio("Navigate", list(pages.keys()))

    pages[selection]()


if __name__ == "__main__":
    main()
