from db_utils import get_data
import seaborn as sns
import matplotlib.pyplot as plt

query_pop = """
SELECT 
    ar.artist_popularity,
    a.album_popularity
FROM albums_data a
JOIN tracks_data t ON a.track_id = t.id
JOIN artist_data ar ON a.artist_id = ar.id
"""
df_pop = get_data(query_pop)

# Correlation and Plot
print("Correlation:", df_pop.corr())
sns.scatterplot(x='artist_popularity', y='album_popularity', data=df_pop)
plt.title("Artist vs Album Popularity")
plt.show()
plt.savefig("artist_vs_album_popularity.png")