import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.formula.api as smf
from matplotlib.widgets import TextBox

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
plt.barh(top_popularity["name"], top_popularity["artist_popularity"])
plt.title("Top 10 Artists by Popularity")
plt.xlabel("Popularity")
plt.gca().invert_yaxis() # flip so 1st artist is on top (gca - get current axes flip so 1st artist is on top)
plt.tight_layout() # adjust layout to prevent overlap
plt.show()

# Plot followers
plt.figure(figsize=(10, 5))
plt.barh(top_followers["name"], top_followers["followers"])
plt.title("Top 10 Artists by Followers")
plt.xlabel("Followers")
plt.gca().invert_yaxis()
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
plt.scatter(df["log_followers"], df["artist_popularity"], alpha=0.5)
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
# Function to get top artists by genre
def top_artists_by_genre(genre):
    # Filter artists where any genre column contains the input genre
    mask = df[["genre_0", "genre_1", "genre_2", "genre_3", "genre_4"]].apply(
        lambda col: col.str.contains(genre, case=False, na=False)
    ).any(axis=1)
    
    filtered = df[mask].nlargest(10, "artist_popularity")[["name", "artist_popularity", "followers"]]
    print(f"Top 10 artists in genre: {genre}")
    print(filtered.to_string(index=False))

# Test it
top_artists_by_genre("pop")
top_artists_by_genre("rock")

# Cool interactive plot to explore genres

fig, ax = plt.subplots(figsize=(10, 6))
plt.subplots_adjust(bottom=0.2)

def update_genre(genre):
    ax.clear()
    mask = df[["genre_0", "genre_1", "genre_2", "genre_3", "genre_4"]].apply(
        lambda col: col.str.contains(genre, case=False, na=False)
    ).any(axis=1)
    
    filtered = df[mask].nlargest(10, "artist_popularity")
    
    if filtered.empty:
        ax.set_title(f"No artists found for: {genre}")
    else:
        ax.barh(filtered["name"], filtered["artist_popularity"], color="#1DB954")
        ax.set_title(f"Top 10 Artists in: {genre}")
        ax.set_xlabel("Popularity")
        ax.invert_yaxis()
    fig.canvas.draw()

# Text box to type genre
ax_box = plt.axes([0.2, 0.05, 0.6, 0.07])
text_box = TextBox(ax_box, "Genre: ", initial="pop")
text_box.ax.set_facecolor("black")
text_box.text_disp.set_color("#1DB954")
text_box.on_submit(update_genre)
update_genre("pop")
plt.show()



