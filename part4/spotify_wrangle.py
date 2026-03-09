
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Connect to the database.
conn = sqlite3.connect("data/spotify_database.db")

tracks = pd.read_sql("SELECT * FROM tracks_data", conn)
features = pd.read_sql("SELECT * FROM features_data", conn)
artists = pd.read_sql("SELECT * FROM artist_data", conn)
albums = pd.read_sql("SELECT * FROM albums_data", conn)


conn.close()

df = tracks.merge(features, on="id", how="inner")

# tracking popularity of artists using the quantiles.
Q1 = df["track_popularity"].quantile(0.25)
Q3 = df["track_popularity"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

pop_outliers = df[(df["track_popularity"] < lower) | 
                  (df["track_popularity"] > upper)]

print("Track popularity outliers:", len(pop_outliers))

# tracking energy of tracks using the quantiles.

Q1 = df["energy"].quantile(0.25)
Q3 = df["energy"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

energy_outliers = df[(df["energy"] < lower) | 
                     (df["energy"] > upper)]

print("Energy outliers:", len(energy_outliers))

#adding artist popularity to the dataframe.

Q1 = artists["artist_popularity"].quantile(0.25)
Q3 = artists["artist_popularity"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

artist_outliers = artists[(artists["artist_popularity"] < lower) |
                          (artists["artist_popularity"] > upper)]

print("Artist popularity outliers:", len(artist_outliers))

#removing invalid ids(tracks, albums, features, tracks with missing features, duplicate ids, and negative durations).

tracks_clean = tracks.dropna(subset=["id"])
tracks_clean = tracks_clean[tracks_clean["id"].str.len() > 0]

albums_clean = albums.dropna(subset=["track_id"])
albums_clean = albums_clean[albums_clean["track_id"].str.len() > 0]

features_clean = features.dropna(subset=["id"])
features_clean = features_clean[features_clean["id"].str.len() > 0]

albums_clean = albums_clean[albums_clean["duration_ms"] > 0]
features_clean = features_clean[features_clean["duration_ms"] > 0]

tracks_clean = tracks_clean.drop_duplicates(subset=["id"])
albums_clean = albums_clean.drop_duplicates(subset=["track_id"])
features_clean = features_clean.drop_duplicates(subset=["id"])

#Only a small number of invalid records were found. 
# Tracks and features contained no missing identifiers 
# and no non-positive durations. A small number of album 
# rows were removed due to invalid or duplicated track identifiers.
#  Outlier detection on artist popularity identified 7 extreme artists.



albums_clean["release_date"] = pd.to_datetime(albums_clean["release_date"], errors="coerce")
albums_clean["year"] = albums_clean["release_date"].dt.year
albums_clean = albums_clean.dropna(subset=["year"])
albums_clean["year"] = albums_clean["year"].astype(int)

time_df = albums_clean.merge(features_clean, left_on="track_id", right_on="id", how="inner")
yearly_avg = time_df.groupby("year")[["energy", "danceability", "valence", "tempo"]].mean()


yearly_avg[["energy", "danceability", "valence"]].plot(figsize=(10,6))
plt.title("Energy, Danceability, Valence over time")
plt.show()

yearly_avg["tempo"].plot(figsize=(10,6))
plt.title("Tempo over time")
plt.show()

#To investigate whether music changed over time, we computed the yearly average of several audio features. 
# The results show that energy and danceability have generally increased over time,
#  indicating that modern music tends to be more energetic and rhythm-oriented. 
# Tempo increased historically but has remained relatively stable in recent decades.
#  Valence shows a slight downward trend, suggesting that recent music may be less positive on average.
#  However,  fluctuations in early years may be due to smaller sample sizes. (in 1945 especiallly which
#i guess people during the world war 2 were not making as much music....)


#Album feature summary.

def album_feature_summary(album_name):
    
    
    album_df = albums_clean[albums_clean["album_name"] == album_name]
    
    if len(album_df) == 0:
        print("Album not found.")
        return
    
   
    merged = album_df.merge(features_clean, left_on="track_id", right_on="id", how="inner")
    
    
    feature_cols = ["energy", "danceability", "valence", "tempo", "loudness"]
    feature_cols = [c for c in feature_cols if c in merged.columns]
    
    summary = merged[feature_cols].mean()
    
    print(f"\nFeature summary for album: {album_name}")
    print(summary)

album_feature_summary("Future Nostalgia")
# results
#Feature summary for album: Future Nostalgia
#nergy            0.741000
#anceability      0.648976
#valence          0.627561
#tempo          128.168951
#loudness     -4.648537
#dtype : float64


#The album feature summary was computed by averaging the audio features
#  of all tracks belonging to the selected album. 
# For example, Future Nostalgia shows high energy and danceability, a relatively fast tempo, 
# and a generally positive mood, which is consistent with modern pop music characteristics.


# Check the artists data for duplicates. 

conn = sqlite3.connect("data/spotify_database.db")
artists = pd.read_sql("SELECT id, name FROM artist_data", conn)
conn.close() #(it was taking too long...)


artists["name_clean"] = artists["name"].str.strip().str.lower()
duplicate_names = artists[artists.duplicated("name_clean", keep=False)]

print("Number of duplicated artist names:", duplicate_names["name_clean"].nunique())

problem_artists = (
    artists.groupby("name_clean")["id"]
    .nunique()
    .reset_index()
)

problem_artists = problem_artists[problem_artists["id"] > 1]

print(problem_artists)

'''
Duplicated names: 159
Names with multiple IDs: 159
'''

# Group the features by the era

def assign_era(year):
    if year < 1970:
        return "Pre-1970"
    elif year < 1990:
        return "1970-1989"
    elif year < 2010:
        return "1990-2009"
    else:
        return "2010+"

albums_clean["era"] = albums_clean["year"].apply(assign_era)
era_df = albums_clean.merge(features_clean, left_on="track_id", right_on="id", how="inner")
era_order = ["Pre-1970", "1970-1989", "1990-2009", "2010+"]
era_df["era"] = pd.Categorical(era_df["era"], categories=era_order, ordered=True)
era_avg = era_df.groupby("era")[["energy", "danceability", "valence", "tempo"]].mean()

print(era_avg)

era_avg[["energy", "danceability", "valence"]].plot(kind="bar", figsize=(8,5))
plt.title("Average Energy, Danceability, Valence by Era")
plt.ylabel("Average Value")
plt.show()

era_avg["tempo"].plot(kind="bar", figsize=(8,5))
plt.title("Average Tempo by Era")
plt.ylabel("Average BPM")
plt.show()

'''
To analyze differences across historical periods,
 the release year of each track was used to assign an era category 
 (Pre-1970, 1970–1989, 1990–2009, 2010+). 
 The dataset was then merged with the audio feature data, and the average values of selected features 
 (energy, danceability, valence, tempo) were computed for each era.
 Bar plots were created to compare these averages across eras.
The results show that energy and danceability have generally increased over time, as we already observed.
'''


#Aggregate popularity and streams by month

albums_clean["release_date"] = pd.to_datetime(albums_clean["release_date"], errors="coerce")
albums_clean = albums_clean.dropna(subset=["release_date"])
albums_clean = albums_clean[albums_clean["release_date"].dt.year >= 1960]
albums_clean["year"] = albums_clean["release_date"].dt.year

pop_df = albums_clean.merge(tracks_clean, left_on="track_id", right_on="id", how="inner")
yearly_popularity = pop_df.groupby("year")["track_popularity"].mean()

yearly_popularity.plot(figsize=(10, 6))
plt.title("Average Track Popularity by Year")
plt.xlabel("Year")
plt.ylabel("Average Popularity")
plt.tight_layout()
plt.show()
'''
We converted the release_date column to a datetime format and extracted the release year.
We filtered out very early years to avoid unstable averages caused by small sample sizes.
Then we merged the album data with the track data to obtain track popularity.
Finally, we grouped the data by year and computed the average track popularity for each year.
The results were visualized using a line plot.
The yearly aggregation shows that average track popularity fluctuates over time. 
Earlier decades display more variability due to fewer observations.
 In more recent years, popularity appears more stable, suggesting a more consistent 
 distribution of popular tracks.
Overall, while popularity changes across years, there is no extreme long-term upward or downward trend; 
instead, the values remain within a moderate range in recent decades.


'''


# dentify the genres that appear together most frequently.

conn = sqlite3.connect("data/spotify_database.db")
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
            a = genres[i]
            b = genres[j]
            if a > b:
                a, b = b, a
            key = (a, b)
            pair_counts[key] = pair_counts.get(key, 0) + 1

pair_df = pd.DataFrame(
    [(k[0], k[1], v) for k, v in pair_counts.items()],
    columns=["genre_1", "genre_2", "count"]
)

pair_df = pair_df.sort_values("count", ascending=False)

print(pair_df.head(10))


'''
To identify genres that frequently appear together, we collected all genre columns from the artist dataset. 
For each artist, we extracted their listed genres and generated all possible genre pairs. 
We then counted how often each pair occurred across all artists and sorted the results by frequency.
The results show that closely related genres frequently appear together. 
For example, hip hop and rap, as well as dance pop and pop, commonly co-occur, which reflects strong stylistic overlap. 
Similarly, electronic genres such as EDM and electro house often appear together.
Latin genres such as trap latino and urbano latino also show high co-occurrence. 
This suggests that genre classifications often group similar or closely connected musical styles.

'''

# identify genres that occur frequently among tracks that score very low or very high. (we choose energy for this one)

conn = sqlite3.connect("data/spotify_database.db")

tracks = pd.read_sql("SELECT * FROM tracks_data", conn)
features = pd.read_sql("SELECT id, energy FROM features_data", conn)
artists = pd.read_sql("SELECT id, name FROM artist_data", conn)
artist_full = pd.read_sql("SELECT * FROM artist_data", conn)
albums = pd.read_sql("SELECT track_id, artist_id FROM albums_data", conn)

conn.close()

df = tracks.merge(features, on="id", how="inner")
df = df.merge(albums, left_on="id", right_on="track_id", how="inner")
df = df.merge(artist_full, left_on="artist_id", right_on="id", how="inner")

df["energy_label"] = pd.qcut(
    df["energy"],
    q=5,
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

very_low = df[df["energy_label"] == "very low"]
very_high = df[df["energy_label"] == "very high"]

print("Top genres for VERY LOW energy:")
print(collect_genres(very_low))

print("\nTop genres for VERY HIGH energy:")
print(collect_genres(very_high))

'''
We selected energy as the numerical feature and divided tracks 
into five equal categories using quantiles: very low, low, medium, high, and very high. 
This ensures that each category contains approximately the same number of tracks. We then identified 
the genres that occur most frequently among tracks classified as very low energy and very high energy. 
Genre frequencies were computed by counting occurrences across all genre columns for the selected subsets.
The analysis shows a clear relationship between energy levels and genre classification. 
Low-energy tracks are predominantly found in classical and jazz-related genres, 
while high-energy tracks are concentrated in pop, rock, electronic, and rap genres. This demonstrates 
that numerical audio features meaningfully reflect stylistic differences across musical genres


'''