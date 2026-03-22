import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.formula.api as smf
from matplotlib.widgets import TextBox
from collections import Counter 

# Load the data
df = pd.read_csv("data/artist_data.csv")

# Filter out junk data
df = df[(df["followers"] > 0) & (df["artist_popularity"] > 0) & (df["name"] != "Various Artists")]

# Spotify green and dark background for better aesthetics
plt.style.use("dark_background")
plt.rcParams["axes.prop_cycle"] = plt.cycler(color=["#1DB954"])

print(df.columns.tolist())

# Basic inspection of the data
print(df.head())  
print(df.shape) # number of rows and columns 

print("Data types:")
print(df.dtypes) # data types in each column

print("Missing values")
print(df.isnull().sum()) # Check for missing values

print("Unique values in each column:")
print(df.nunique()) # Unique values in each column

print("Unique artists:", df['name'].nunique()) 

# Top 10 by popularity
top_popularity = df.nlargest(10, "artist_popularity")[["name", "artist_popularity"]]

# Top 10 by followers
top_followers = df.nlargest(10, "followers")[["name", "followers"]]

# Plot popularity
plt.figure(figsize=(10, 5))
plt.barh(top_popularity["name"], top_popularity["artist_popularity"], color="#1DB954")
plt.title("Top 10 Artists by Popularity")
plt.xlabel("Popularity score (0-100)")
plt.gca().invert_yaxis()

for bar in plt.gca().patches:
    plt.gca().text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                   f"{bar.get_width():.0f}", va="center", fontsize=9, color="white")

plt.xlim(0, top_popularity["artist_popularity"].max() + 5)
plt.tight_layout()
plt.show()

# Plot followers
plt.figure(figsize=(10, 5))
# Convert followers to millions to make the axis more readable
top_followers_millions = top_followers.copy()
top_followers_millions["followers_m"] = top_followers_millions["followers"] / 1_000_000

plt.barh(top_followers_millions["name"], top_followers_millions["followers_m"])
plt.title("Top 10 Artists by Followers")
plt.xlabel("Followers (millions)")
plt.gca().invert_yaxis()

# Add value labels
for i, value in enumerate(top_followers_millions["followers_m"]):
    plt.text(value + 0.5, i, f"{value:.1f}M", va="center", fontsize=9)

plt.tight_layout()
plt.show()

# Popularity vs followers
# We use log scale for followers to handle the wide range of values and make the plot more interpretable
df["log_followers"] = np.log1p(df["followers"]) # log1p to handle zero followers

# Correlation 
correlation = df["artist_popularity"].corr(df["log_followers"])
print("Correlation between popularity and log followers:", correlation)

# Using the OLS 
model = smf.ols("artist_popularity ~ log_followers", data=df).fit()
print(model.summary())

# B0 and B1
print("B0 (intercept):", model.params["Intercept"])
print("B1 (slope):", model.params["log_followers"], "\n")

# Scatter plot with regression line
plt.figure(figsize=(10, 5))
plt.scatter(df["log_followers"], df["artist_popularity"], alpha=0.5) # alpha here defines the transparency of the points
plt.plot(df["log_followers"], model.fittedvalues, color="white") # regression line
plt.title("Popularity vs Followers")
plt.xlabel("Followers (log scale)")
plt.ylabel("Popularity")
plt.show()

# Over-performers and Legacy artists

# Computing the residuals
df["residuals"] = model.resid 

# Over-performers (positive residuals) 
over_performers = df[df["residuals"] > 0].nlargest(10, "residuals")[["name", "artist_popularity", "followers", "log_followers", "residuals"]]
print("Top 10 Over-Performers:", over_performers, "\n")

# Legacy artists (negative residuals)
legacy_artists = df[df["residuals"] < 0].nsmallest(10, "residuals")[["name", "artist_popularity", "followers","log_followers", "residuals"]]
print("Top 10 Legacy Artists:", legacy_artists, "\n")

# Plot the Overperformers and Legacy artists on the scatter plot
# Scatter plot with highlighted groups
plt.figure(figsize=(12, 7))

# All artists in grey
plt.scatter(df["log_followers"], df["artist_popularity"], 
            alpha=0.3, color="#145214", label="All artists")

# Highlight over-performers in green
plt.scatter(over_performers["log_followers"], over_performers["artist_popularity"],
            color="#1DB954", s=100, label="Over-performers", zorder=5)

# Highlight legacy artists in red
plt.scatter(legacy_artists["log_followers"], legacy_artists["artist_popularity"],
            color="red", s=100, label="Legacy artists", zorder=5)

# Regression line 
plt.plot(df["log_followers"].sort_values(),
         model.fittedvalues.sort_values(), linewidth=2, color="white")

plt.suptitle("Popularity vs Followers - Over-performers & Legacy Artists", fontsize=13)
plt.title("Green = more popular than expected , Red = less popular than expected", fontsize=9, color="grey")
plt.xlabel("Followers (log scale)")
plt.ylabel("Popularity")
plt.legend()
plt.tight_layout()
plt.show()

# Relevance of genres
# Automatically detect all usable genre columns
genre_cols = [col for col in df.columns if col.startswith("genre_")]
genre_cols = [col for col in genre_cols if not df[col].isna().all()]
print("Genre columns used:", genre_cols)

# Create a clean list of genres for each artist
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

# Show most common genres as a useful summary
all_genres = [g for sublist in df["genres_list"] for g in sublist]
genre_counts = Counter(all_genres)

genre_freq = pd.DataFrame(genre_counts.most_common(15), columns=["genre", "count"])
print("\nTop 15 most common genres:")
print(genre_freq.to_string(index=False))

# Helper function to filter artists by genre
def get_artists_by_genre(genre):
    genre = genre.strip().lower()
    mask = df["genres_list"].apply(
        lambda lst: any(str(x).lower() == genre for x in lst)
    )
    return df[mask].nlargest(10, "artist_popularity")

# Prints top 10 artists in a genre to terminal
def top_artists_by_genre(genre):
    filtered = get_artists_by_genre(genre)
    print(f"Top 10 artists in genre: {genre}")
    print(filtered[["name", "artist_popularity", "followers"]].to_string(index=False))

# Interactive plot to explore genres
fig, ax = plt.subplots(figsize=(10, 6))
plt.subplots_adjust(bottom=0.2)

def update_genre(genre):
    ax.clear()
    filtered = get_artists_by_genre(genre)
    if filtered.empty:
        ax.set_title(f"No artists found for: {genre}")
    else:
        ax.barh(filtered["name"], filtered["artist_popularity"], color="#1DB954")
        ax.set_title(f"Top 10 Artists in: {genre}")
        ax.set_xlabel("Popularity")
        ax.invert_yaxis()
    fig.canvas.draw()

ax_box = plt.axes([0.2, 0.05, 0.6, 0.07])
text_box = TextBox(ax_box, "Genre: ", initial="pop")
text_box.ax.set_facecolor("black")
text_box.text_disp.set_color("#1DB954")
text_box.on_submit(update_genre)
update_genre("pop")
plt.show()

# Count number of genres per artist
df["num_genres"] = df["genres_list"].apply(len)
print(df[["name", "num_genres"]].head())

# Print summary and correlations for number of genres
print("\nSummary statistics for number of genres:")
print(df["num_genres"].describe())

print("\nCorrelation between number of genres and popularity:", df["num_genres"].corr(df["artist_popularity"]))
print("Correlation between number of genres and followers:", df["num_genres"].corr(df["followers"]))
print("Correlation between number of genres and log followers:", df["num_genres"].corr(df["log_followers"]))

# Scatter plot: number of genres vs popularity
plt.figure(figsize=(10, 5))
plt.scatter(df["num_genres"], df["artist_popularity"], alpha=0.4)
plt.title("Number of Genres vs Popularity")
plt.xlabel("Number of genres")
plt.ylabel("Popularity")
plt.tight_layout()
plt.show()

# Scatter plot: number of genres vs followers
plt.figure(figsize=(10, 5))
plt.scatter(df["num_genres"], df["followers"], alpha=0.4)
plt.title("Number of Genres vs Followers")
plt.xlabel("Number of genres")
plt.ylabel("Followers")
plt.yscale("log")  # makes followers easier to read
plt.tight_layout()
plt.show()

# Extra creative insight:
# divide artists into follower-size groups and compare popularity
df["follower_bins"] = pd.qcut(df["followers"], 5, duplicates="drop")

grouped_popularity = df.groupby("follower_bins", observed=False)["artist_popularity"].median()

plt.figure(figsize=(10, 5))
grouped_popularity.plot(kind="bar")
plt.title("Median Popularity Across Follower Size Groups")
plt.xlabel("Follower size group")
plt.ylabel("Median popularity")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

