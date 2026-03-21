import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.formula.api as smf
from matplotlib.widgets import TextBox
from collections import Counter 

# Function for loading the data
def load_data():
    import os
    csv_path = "../data/artist_data.csv"
    if not os.path.exists(csv_path):
        _this_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(os.path.dirname(_this_dir), "data", "artist_data.csv")
    df = pd.read_csv(csv_path)
    # Filter out junk data
    df = df[(df["followers"] > 0) & (df["artist_popularity"] > 0) & (df["name"] != "Various Artists")].copy()
    return df

# Function for getting top popularity
def get_top_popularity(df):
    top_popularity = df.nlargest(10, "artist_popularity")[["name", "artist_popularity"]]
    return top_popularity

# Function for getting top followers
def get_top_followers(df):
    top_followers = df.nlargest(10, "followers")[["name", "followers"]]
    return top_followers

# Function for plotting popularity
def plot_popularity(df):
    top_popularity = get_top_popularity(df)

    fig, ax = plt.subplots(figsize=(10, 5))

    # Set dark background
    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    ax.barh(top_popularity["name"], top_popularity["artist_popularity"], color="#1DB954")
    ax.set_title("Top 10 Artists by Popularity", color="white")
    ax.set_xlabel("Popularity score (0-100)", color="white")
    ax.set_ylabel("Artist Name", color="white")

    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white") 

    ax.invert_yaxis()

    for bar in ax.patches:
        ax.text(
            bar.get_width() + 0.8,
            bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.0f}",
            va="center",
            fontsize=9,
            color="white"
        )
        
    # make border lines white
    for spine in ax.spines.values():
        spine.set_color("white")

    ax.set_xlim(0, top_popularity["artist_popularity"].max() + 5)
    plt.tight_layout()
    return fig

# Function for plotting followers
def plot_followers(df):
    top_followers = get_top_followers(df).copy()
    top_followers["followers_m"] = top_followers["followers"] / 1_000_000

    fig, ax = plt.subplots(figsize=(10, 5))

    # Dark background
    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    ax.barh(top_followers["name"], top_followers["followers_m"], color="#1DB954")
    ax.set_title("Top 10 Artists by Followers", color="white")
    ax.set_xlabel("Followers (millions)", color="white")
    ax.set_ylabel("Artist Name", color="white")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    ax.invert_yaxis()

    for i, value in enumerate(top_followers["followers_m"]):
        ax.text(value + 0.5, i, f"{value:.1f}M", va="center", fontsize=9, color="white")
    
    # make border lines white
    for spine in ax.spines.values():
        spine.set_color("white")

    plt.tight_layout()
    return fig


# Popularity vs followers

# Add log followers to the dataframe
def add_log_followers(df):
    df = df.copy()
    df["log_followers"] = np.log1p(df["followers"])
    return df

# Get correlation between popularity and log followers
def get_correlation(df):
    df = add_log_followers(df)
    correlation = df["artist_popularity"].corr(df["log_followers"])
    return correlation

# Fit OLS model
def fit_model(df):
    df = add_log_followers(df)
    model = smf.ols("artist_popularity ~ log_followers", data=df).fit()
    return model

# Print model results
def print_model_results(df):
    df = add_log_followers(df)
    model = fit_model(df)

    correlation = df["artist_popularity"].corr(df["log_followers"])
    print("Correlation between popularity and log followers:", correlation)
    print(model.summary())
    print("B0 (intercept):", model.params["Intercept"])
    print("B1 (slope):", model.params["log_followers"])

# Plot popularity vs followers with regression line
def plot_popularity_vs_followers(df):
    df = add_log_followers(df)
    model = fit_model(df)

    fig, ax = plt.subplots(figsize=(10, 5))

    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    ax.scatter(df["log_followers"], df["artist_popularity"], alpha=0.5, color="#1DB954")
    ax.plot(df["log_followers"], model.fittedvalues, color="white")

    ax.set_title("Popularity vs Followers", color="white")
    ax.set_xlabel("Followers (log scale)", color="white")
    ax.set_ylabel("Popularity", color="white")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    for spine in ax.spines.values():
        spine.set_color("white")

    plt.tight_layout()
    return fig

# Get overperformers and legacy artists based on residuals from the OLS model
def get_overperformers_and_legacy(df):
    df = add_log_followers(df)
    model = fit_model(df)

    df = df.copy()
    df["residuals"] = model.resid

    over_performers = df[df["residuals"] > 0].nlargest(10, "residuals")[["name", "artist_popularity", "followers", "log_followers", "residuals"]]

    legacy_artists = df[df["residuals"] < 0].nsmallest(10, "residuals")[["name", "artist_popularity", "followers", "log_followers", "residuals"]]

    return over_performers, legacy_artists

# Plot overperformers and legacy artists on the scatter plot
def plot_overperformers_legacy(df):
    df = add_log_followers(df)
    model = fit_model(df)

    df = df.copy()
    df["residuals"] = model.resid
    
    # Get the top 10 over-performers and legacy artists
    over_performers = df[df["residuals"] > 0].nlargest(10, "residuals")
    legacy_artists = df[df["residuals"] < 0].nsmallest(10, "residuals")

    # Scatter plot with highlighted groups
    fig, ax = plt.subplots(figsize=(12, 7))

    # Dark background
    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    # Plot all artists in grey
    ax.scatter(
        df["log_followers"],
        df["artist_popularity"],
        alpha=0.3,
        color="#145214",
        label="All artists"
    )

    # Highlight over-performers in green
    ax.scatter(
        over_performers["log_followers"],
        over_performers["artist_popularity"],
        color="#1DB954",
        s=100,
        label="Over-performers",
        zorder=5
    )

    # Highlight legacy artists in red
    ax.scatter(
        legacy_artists["log_followers"],
        legacy_artists["artist_popularity"],
        color="red",
        s=100,
        label="Legacy artists",
        zorder=5
    )

    # Regression line
    ax.plot(
        df["log_followers"].sort_values(),
        model.fittedvalues.sort_values(),
        linewidth=2,
        color="white"
    )
    # Set titles and labels with white color
    ax.set_title("Popularity vs Followers - Over-performers & Legacy Artists", color="white")
    ax.set_xlabel("Followers (log scale)", color="white")
    ax.set_ylabel("Popularity", color="white")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    # Customize legend
    legend = ax.legend()
    for text in legend.get_texts():
        text.set_color("white")

    for spine in ax.spines.values():
        spine.set_color("white")

    plt.tight_layout()
    return fig

# Relevance of genres
# We will create a genres list column by checking for genre columns or parsing the artist_genres column if available. This will allow us to analyze genre relevance in the next steps.
def add_genres_list(df):
    df = df.copy()

    # Find usable genre columns
    genre_cols = [col for col in df.columns if col.startswith("genre_")]
    genre_cols = [col for col in genre_cols if not df[col].isna().all()]

    # Build genre list
    if genre_cols:
        df["genres_list"] = df[genre_cols].apply(
            lambda row: [g for g in row.dropna().tolist() if str(g).strip() != ""],
            axis=1
        )
    elif "artist_genres" in df.columns:
        df["genres_list"] = df["artist_genres"].fillna("").apply(
            lambda x: [g.strip() for g in str(x).split(",") if g.strip() != ""]
        )
    else:
        df["genres_list"] = [[] for _ in range(len(df))]

    return df

# Helper function to filter artists by genre
def get_genre_columns(df):
    genre_cols = [col for col in df.columns if col.startswith("genre_")]
    genre_cols = [col for col in genre_cols if not df[col].isna().all()]
    return genre_cols

# Helper function to get top genres
def get_top_genres(df):
    df = add_genres_list(df)

    all_genres = [g for sublist in df["genres_list"] for g in sublist]
    genre_counts = Counter(all_genres)

    genre_freq = pd.DataFrame(
        genre_counts.most_common(15),
        columns=["genre", "count"]
    )

    return genre_freq

# Helper function to get artists by genre
def get_artists_by_genre(df, genre):
    df = add_genres_list(df)

    genre = genre.strip().lower()

    mask = df["genres_list"].apply(
        lambda lst: any(str(x).lower() == genre for x in lst) 
    )

    return df[mask].nlargest(10, "artist_popularity")

#Plot top genres
def plot_top_genres(df):
    genre_freq = get_top_genres(df)

    fig, ax = plt.subplots(figsize=(10, 5))

    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    ax.barh(genre_freq["genre"], genre_freq["count"], color="#1DB954")
    ax.set_title("Top 15 Most Common Genres", color="white")
    ax.set_xlabel("Count", color="white")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    ax.invert_yaxis()

    for spine in ax.spines.values():
        spine.set_color("white")

    plt.tight_layout()
    return fig

# Plot artists by genre
def plot_artists_by_genre(df, genre):
    filtered = get_artists_by_genre(df, genre)

    fig, ax = plt.subplots(figsize=(10, 5))

    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    if filtered.empty:
        ax.text(
            0.5, 0.5,
            f"No artists found for genre: {genre}",
            ha="center",
            va="center",
            color="white",
            fontsize=12
        )
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.barh(filtered["name"], filtered["artist_popularity"], color="#1DB954")
        ax.set_title(f"Top 10 Artists in: {genre}", color="white")
        ax.set_xlabel("Popularity", color="white")
        ax.tick_params(axis="x", colors="white")
        ax.tick_params(axis="y", colors="white")
        ax.invert_yaxis()

    for spine in ax.spines.values():
        spine.set_color("white")

    plt.tight_layout()
    return fig

# In the Streamlit app, we can use these functions to display the relevant information and plots for the "Genre Explorer" page.
def add_num_genres(df):
    df = df.copy()

    if "genres_list" not in df.columns:
        df = add_genres_list(df)

    df["num_genres"] = df["genres_list"].apply(len)
    return df

# Display the over-performers and legacy artists tables
def get_num_genres_summary(df):
    df = add_num_genres(df)
    
    # Get summary statistics and correlations for number of genres
    summary = {
        "mean_num_genres": df["num_genres"].mean(),
        "median_num_genres": df["num_genres"].median(),
        "max_num_genres": df["num_genres"].max(),
        "corr_popularity": df["num_genres"].corr(df["artist_popularity"]),
        "corr_followers": df["num_genres"].corr(df["followers"])
    }

    if "log_followers" not in df.columns:
        df = add_log_followers(df)

    summary["corr_log_followers"] = df["num_genres"].corr(df["log_followers"])

    return summary

# Plot the number of genres vs popularity and followers
def plot_num_genres_vs_popularity(df):
    df = add_num_genres(df)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    ax.scatter(df["num_genres"], df["artist_popularity"], alpha=0.4, color="#1DB954")
    ax.set_title("Number of Genres vs Popularity", color="white")
    ax.set_xlabel("Number of genres", color="white")
    ax.set_ylabel("Popularity", color="white")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    for spine in ax.spines.values():
        spine.set_color("white")

    plt.tight_layout()
    return fig

# Plot the number of genres vs followers
def plot_num_genres_vs_followers(df):
    df = add_num_genres(df)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    ax.scatter(df["num_genres"], df["followers"], alpha=0.4, color="#1DB954")
    ax.set_title("Number of Genres vs Followers", color="white")
    ax.set_xlabel("Number of genres", color="white")
    ax.set_ylabel("Followers", color="white")
    ax.set_yscale("log")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")

    for spine in ax.spines.values():
        spine.set_color("white")

    plt.tight_layout()
    return fig

# Plot follower groups vs popularity
def plot_follower_groups_vs_popularity(df):
    df = df.copy()
    df["follower_bins"] = pd.qcut(df["followers"], 5, duplicates="drop")
    grouped_popularity = df.groupby("follower_bins", observed=False)["artist_popularity"].median()

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    grouped_popularity.plot(kind="bar", ax=ax, color="#1DB954")

    ax.set_title("Median Popularity Across Follower Size Groups", color="white")
    ax.set_xlabel("Follower size group", color="white")
    ax.set_ylabel("Median popularity", color="white")
    ax.tick_params(axis="x", colors="white", rotation=45)
    ax.tick_params(axis="y", colors="white")

    for spine in ax.spines.values():
        spine.set_color("white")

    plt.tight_layout()
    return fig