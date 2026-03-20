import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

# ──────────────────────────────────────────────────────────────────
# Database connection
# ──────────────────────────────────────────────────────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
_DB_PATH = os.path.join(_THIS_DIR, "data", "spotify_database.db")
if not os.path.exists(_DB_PATH):
    _DB_PATH = os.path.join(_PROJECT_ROOT, "data", "spotify_database.db")


def _connect():
    return sqlite3.connect(_DB_PATH)


# ──────────────────────────────────────────────────────────────────
# Data loading and cleaning
# ──────────────────────────────────────────────────────────────────
def load_all_tables():
    """Load all four tables from the database and return them as DataFrames."""
    conn = _connect()
    tracks = pd.read_sql("SELECT * FROM tracks_data", conn)
    features = pd.read_sql("SELECT * FROM features_data", conn)
    artists = pd.read_sql("SELECT * FROM artist_data", conn)
    albums = pd.read_sql("SELECT * FROM albums_data", conn)
    conn.close()
    return tracks, features, artists, albums


def clean_data(tracks, features, albums):
    """Remove invalid records: missing IDs, negative durations, duplicates.
    Returns (tracks_clean, features_clean, albums_clean)."""
    tracks_clean = tracks.dropna(subset=["id"])
    tracks_clean = tracks_clean[tracks_clean["id"].str.len() > 0]
    tracks_clean = tracks_clean.drop_duplicates(subset=["id"])

    albums_clean = albums.dropna(subset=["track_id"])
    albums_clean = albums_clean[albums_clean["track_id"].str.len() > 0]
    albums_clean = albums_clean[albums_clean["duration_ms"] > 0]
    albums_clean = albums_clean.drop_duplicates(subset=["track_id"])

    features_clean = features.dropna(subset=["id"])
    features_clean = features_clean[features_clean["id"].str.len() > 0]
    features_clean = features_clean[features_clean["duration_ms"] > 0]
    features_clean = features_clean.drop_duplicates(subset=["id"])

    return tracks_clean, features_clean, albums_clean


# ──────────────────────────────────────────────────────────────────
# Outlier detection
# ──────────────────────────────────────────────────────────────────
def detect_outliers_iqr(df, column):
    """Detect outliers using the IQR method.
    Returns (outlier_df, stats_dict) where stats_dict has Q1, Q3, IQR, lower, upper."""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    outliers = df[(df[column] < lower) | (df[column] > upper)]

    stats = {"Q1": Q1, "Q3": Q3, "IQR": IQR, "lower": lower, "upper": upper,
             "count": len(outliers)}
    return outliers, stats


# ──────────────────────────────────────────────────────────────────
# Era assignment
# ──────────────────────────────────────────────────────────────────
def assign_era(year):
    """Categorize a release year into an era label."""
    if year < 1970:
        return "Pre-1970"
    elif year < 1990:
        return "1970-1989"
    elif year < 2010:
        return "1990-2009"
    else:
        return "2010+"


def add_era_column(albums_clean):
    """Add 'year' and 'era' columns to albums_clean.
    Returns the modified DataFrame."""
    albums_clean = albums_clean.copy()
    albums_clean["release_date"] = pd.to_datetime(albums_clean["release_date"], errors="coerce")
    albums_clean["year"] = albums_clean["release_date"].dt.year
    albums_clean = albums_clean.dropna(subset=["year"])
    albums_clean["year"] = albums_clean["year"].astype(int)
    albums_clean["era"] = albums_clean["year"].apply(assign_era)
    return albums_clean


# ──────────────────────────────────────────────────────────────────
# Feature trends over time
# ──────────────────────────────────────────────────────────────────
def get_feature_trends(albums_clean, features_clean,
                       feature_cols=None):
    """Compute yearly averages of audio features.
    Returns a DataFrame indexed by year."""
    if feature_cols is None:
        feature_cols = ["energy", "danceability", "valence", "tempo"]

    time_df = albums_clean.merge(features_clean, left_on="track_id", right_on="id", how="inner")
    yearly_avg = time_df.groupby("year")[feature_cols].mean()
    return yearly_avg


def plot_feature_trends(yearly_avg, features=None):
    """Plot feature trends over time. Returns list of figures."""
    if features is None:
        features = ["energy", "danceability", "valence"]

    figs = []
    fig, ax = plt.subplots(figsize=(10, 6))
    yearly_avg[features].plot(ax=ax)
    ax.set_title("Audio Features Over Time")
    figs.append(fig)

    if "tempo" in yearly_avg.columns:
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        yearly_avg["tempo"].plot(ax=ax2)
        ax2.set_title("Tempo Over Time")
        figs.append(fig2)

    return figs


# ──────────────────────────────────────────────────────────────────
# Album feature summary
# ──────────────────────────────────────────────────────────────────
def album_feature_summary(album_name, albums_clean=None, features_clean=None):
    """Return the average audio features for a given album as a Series.
    If albums_clean and features_clean are not provided, loads from DB."""
    if albums_clean is None or features_clean is None:
        tracks, features_clean, artists, albums = load_all_tables()
        _, features_clean, albums_clean = clean_data(tracks, features_clean, albums)

    album_df = albums_clean[albums_clean["album_name"] == album_name]

    if len(album_df) == 0:
        print("Album not found.")
        return None

    merged = album_df.merge(features_clean, left_on="track_id", right_on="id", how="inner")

    feature_cols = ["energy", "danceability", "valence", "tempo", "loudness"]
    feature_cols = [c for c in feature_cols if c in merged.columns]

    summary = merged[feature_cols].mean()
    return summary


# ──────────────────────────────────────────────────────────────────
# Duplicate artist detection
# ──────────────────────────────────────────────────────────────────
def find_duplicate_artists():
    """Find artist names that appear with multiple IDs.
    Returns (duplicate_names_df, problem_artists_df)."""
    conn = _connect()
    artists = pd.read_sql("SELECT id, name FROM artist_data", conn)
    conn.close()

    artists["name_clean"] = artists["name"].str.strip().str.lower()
    duplicate_names = artists[artists.duplicated("name_clean", keep=False)]

    problem_artists = (
        artists.groupby("name_clean")["id"]
        .nunique()
        .reset_index()
    )
    problem_artists = problem_artists[problem_artists["id"] > 1]

    return duplicate_names, problem_artists


# ──────────────────────────────────────────────────────────────────
# Era-based feature comparison
# ──────────────────────────────────────────────────────────────────
def get_era_features(albums_clean, features_clean,
                     feature_cols=None):
    """Compute average features grouped by era.
    Returns a DataFrame with era as index."""
    if feature_cols is None:
        feature_cols = ["energy", "danceability", "valence", "tempo"]

    era_df = albums_clean.merge(features_clean, left_on="track_id", right_on="id", how="inner")
    era_order = ["Pre-1970", "1970-1989", "1990-2009", "2010+"]
    era_df["era"] = pd.Categorical(era_df["era"], categories=era_order, ordered=True)
    era_avg = era_df.groupby("era")[feature_cols].mean()
    return era_avg


def plot_era_features(era_avg):
    """Create bar plots of features by era. Returns list of figures."""
    figs = []
    cols = [c for c in ["energy", "danceability", "valence"] if c in era_avg.columns]
    if cols:
        fig, ax = plt.subplots(figsize=(8, 5))
        era_avg[cols].plot(kind="bar", ax=ax)
        ax.set_title("Average Energy, Danceability, Valence by Era")
        ax.set_ylabel("Average Value")
        figs.append(fig)

    if "tempo" in era_avg.columns:
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        era_avg["tempo"].plot(kind="bar", ax=ax2)
        ax2.set_title("Average Tempo by Era")
        ax2.set_ylabel("Average BPM")
        figs.append(fig2)

    return figs


# ──────────────────────────────────────────────────────────────────
# Yearly popularity
# ──────────────────────────────────────────────────────────────────
def get_yearly_popularity(albums_clean, tracks_clean):
    """Compute average track popularity by release year.
    Returns a Series indexed by year."""
    ac = albums_clean.copy()
    ac["release_date"] = pd.to_datetime(ac["release_date"], errors="coerce")
    ac = ac.dropna(subset=["release_date"])
    ac = ac[ac["release_date"].dt.year >= 1960]
    ac["year"] = ac["release_date"].dt.year.astype(int)

    pop_df = ac.merge(tracks_clean, left_on="track_id", right_on="id", how="inner")
    yearly_popularity = pop_df.groupby("year")["track_popularity"].mean()
    return yearly_popularity


# ──────────────────────────────────────────────────────────────────
# Genre pair co-occurrence
# ──────────────────────────────────────────────────────────────────
def find_genre_pairs():
    """Find genres that appear together most frequently.
    Returns a DataFrame with columns (genre_1, genre_2, count)."""
    conn = _connect()
    artists = pd.read_sql("SELECT * FROM artist_data", conn)
    conn.close()

    genre_cols = [c for c in artists.columns if c.startswith("genre_")]

    pair_counts = {}
    for _, row in artists.iterrows():
        genres = []
        for col in genre_cols:
            val = row[col]
            if pd.notna(val):
                g = str(val).strip().lower()
                if g != "":
                    genres.append(g)

        genres = list(set(genres))
        for i in range(len(genres)):
            for j in range(i + 1, len(genres)):
                a, b = genres[i], genres[j]
                if a > b:
                    a, b = b, a
                key = (a, b)
                pair_counts[key] = pair_counts.get(key, 0) + 1

    pair_df = pd.DataFrame(
        [(k[0], k[1], v) for k, v in pair_counts.items()],
        columns=["genre_1", "genre_2", "count"]
    )
    pair_df = pair_df.sort_values("count", ascending=False)
    return pair_df


# ──────────────────────────────────────────────────────────────────
# Feature-based track labeling
# ──────────────────────────────────────────────────────────────────
def label_tracks_by_feature(feature_name="energy"):
    """Label tracks into quintiles for a given feature.
    Returns (very_low_genres, very_high_genres, full_df)."""
    conn = _connect()
    tracks = pd.read_sql("SELECT * FROM tracks_data", conn)
    features = pd.read_sql(f"SELECT id, {feature_name} FROM features_data", conn)
    artist_full = pd.read_sql("SELECT * FROM artist_data", conn)
    albums = pd.read_sql("SELECT track_id, artist_id FROM albums_data", conn)
    conn.close()

    df = tracks.merge(features, on="id", how="inner")
    df = df.merge(albums, left_on="id", right_on="track_id", how="inner")
    df = df.merge(artist_full, left_on="artist_id", right_on="id", how="inner",
                  suffixes=("", "_artist"))

    df["feature_label"] = pd.qcut(
        df[feature_name], q=5,
        labels=["very low", "low", "medium", "high", "very high"]
    )

    genre_cols = [c for c in df.columns if c.startswith("genre_")]

    def collect_genres(subset):
        genres = []
        for _, row in subset.iterrows():
            for col in genre_cols:
                if pd.notna(row[col]):
                    genres.append(str(row[col]).strip().lower())
        return pd.Series(genres).value_counts().head(10)

    very_low = df[df["feature_label"] == "very low"]
    very_high = df[df["feature_label"] == "very high"]

    return collect_genres(very_low), collect_genres(very_high), df


# ══════════════════════════════════════════════════════════════════
# Main — runs the original Part 4 analysis when executed directly
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    tracks, features, artists, albums = load_all_tables()

    # Merge tracks + features for outlier detection
    df = tracks.merge(features, on="id", how="inner")

    pop_outliers, pop_stats = detect_outliers_iqr(df, "track_popularity")
    print("Track popularity outliers:", pop_stats["count"])

    energy_outliers, energy_stats = detect_outliers_iqr(df, "energy")
    print("Energy outliers:", energy_stats["count"])

    artist_outliers, artist_stats = detect_outliers_iqr(artists, "artist_popularity")
    print("Artist popularity outliers:", artist_stats["count"])

    # Clean data
    tracks_clean, features_clean, albums_clean = clean_data(tracks, features, albums)

    # Add era column
    albums_clean = add_era_column(albums_clean)

    # Feature trends
    yearly_avg = get_feature_trends(albums_clean, features_clean)
    figs = plot_feature_trends(yearly_avg)
    for f in figs:
        plt.show()

    # Album feature summary
    summary = album_feature_summary("Future Nostalgia", albums_clean, features_clean)
    if summary is not None:
        print("\nFeature summary for album: Future Nostalgia")
        print(summary)

    # Duplicate artists
    dup_names, problem = find_duplicate_artists()
    print("Number of duplicated artist names:", dup_names["name_clean"].nunique())
    print(problem)

    # Era features
    era_avg = get_era_features(albums_clean, features_clean)
    print(era_avg)
    era_figs = plot_era_features(era_avg)
    for f in era_figs:
        plt.show()

    # Yearly popularity
    yearly_pop = get_yearly_popularity(albums_clean, tracks_clean)
    fig, ax = plt.subplots(figsize=(10, 6))
    yearly_pop.plot(ax=ax)
    ax.set_title("Average Track Popularity by Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Average Popularity")
    plt.tight_layout()
    plt.show()

    # Genre pairs
    pair_df = find_genre_pairs()
    print(pair_df.head(10))

    # Feature labeling
    vl, vh, labeled_df = label_tracks_by_feature("energy")
    print("Top genres for VERY LOW energy:")
    print(vl)
    print("\nTop genres for VERY HIGH energy:")
    print(vh)
