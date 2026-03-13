import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.api import OLS, add_constant

# Load data
df = pd.read_csv("artist_data.csv")


print("\n--- BASIC INSPECTION ---")
print(df.head(10))
print("\nColumns and data types:")
print(df.dtypes)

unique_artists = df['name'].nunique()
print(f"\nNumber of unique artists: {unique_artists}")

top_popularity = df.sort_values(by='artist_popularity', ascending=False).head(10)

top_followers = df.sort_values(by='followers', ascending=False).head(10)

# Plot Top 10 Popularity
plt.figure(figsize=(10, 5))
sns.barplot(data=top_popularity, x='artist_popularity', y='name')
plt.title("Top 10 Artists by Popularity")
plt.tight_layout()
plt.savefig("top10_popularity.png")
plt.show()

# Plot Top 10 Followers
plt.figure(figsize=(10, 5))
sns.barplot(data=top_followers, x='followers', y='name')
plt.title("Top 10 Artists by Followers")
plt.tight_layout()
plt.savefig("top10_followers.png")
plt.show()

# Popularity vs Followers
df['log_followers'] = np.log(df['followers'] + 1)

correlation = df['artist_popularity'].corr(df['log_followers'])
print(f"\nCorrelation between popularity and log(followers): {correlation:.3f}")

X = add_constant(df['log_followers'])
y = df['artist_popularity']
model = OLS(y, X).fit()
print("\n--- LINEAR REGRESSION RESULTS ---")
print(model.summary())

# Scatter plot
plt.figure(figsize=(8, 6))
sns.scatterplot(x='log_followers', y='artist_popularity', data=df, alpha=0.5)
sns.regplot(x='log_followers', y='artist_popularity', data=df, scatter=False, color='red')
plt.title("Popularity vs Log(Followers)")
plt.tight_layout()
plt.savefig("popularity_vs_followers.png")
plt.show()

# Over-performers & legacy artists
pop_thresh = df['artist_popularity'].quantile(0.9)
fol_thresh = df['followers'].quantile(0.9)

overperformers = df[(df['artist_popularity'] > pop_thresh) & 
                    (df['followers'] < df['followers'].quantile(0.3))]

legacy_artists = df[(df['artist_popularity'] < df['artist_popularity'].quantile(0.3)) & 
                    (df['followers'] > fol_thresh)]

print("\nOver-performers (high popularity, low followers):")
print(overperformers[['name', 'artist_popularity', 'followers']].head())

print("\nLegacy artists (low popularity, high followers):")
print(legacy_artists[['name', 'artist_popularity', 'followers']].head())

# Genre analysis function
def top_artists_by_genre(genre, df):
    genre_df = df[df['artist_genres'].str.contains(genre, case=False, na=False)]
    return genre_df.sort_values(by='artist_popularity', ascending=False).head(10)[
        ['name', 'artist_popularity']
    ]

print("\nExample: Top artists in genre 'pop'")
print(top_artists_by_genre("pop", df))

# Count number of genres per artist
df['num_genres'] = df['artist_genres'].apply(lambda x: len(str(x).split(", ")))

plt.figure(figsize=(8, 5))
sns.histplot(df['num_genres'], bins=20, kde=True)
plt.title("Distribution of Number of Genres per Artist")
plt.tight_layout()
plt.savefig("num_genres_distribution.png")
plt.show()

# Correlations with number of genres
corr_pop = df['num_genres'].corr(df['artist_popularity'])
corr_fol = df['num_genres'].corr(df['followers'])

print(f"\nCorrelation between number of genres and popularity: {corr_pop:.3f}")
print(f"Correlation between number of genres and followers: {corr_fol:.3f}")

# Extra creative insight: Popularity by follower size groups
df['follower_bins'] = pd.qcut(df['followers'], 5)

plt.figure(figsize=(10, 6))
sns.boxplot(x='follower_bins', y='artist_popularity', data=df)
plt.xticks(rotation=45)
plt.title("Popularity Across Follower Size Groups")
plt.tight_layout()
plt.savefig("popularity_by_follower_bins.png")
plt.show()

print("\nAll figures have been saved to the current directory.")
