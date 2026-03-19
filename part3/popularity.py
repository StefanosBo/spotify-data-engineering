from db_utils import get_data
import seaborn as sns
import matplotlib.pyplot as plt

def analyze_popularity():
    """Analyze the relationship between artist popularity and album popularity.
    Returns (df_pop, correlation, figure)."""
    query_pop = """
    SELECT 
        ar.artist_popularity,
        a.album_popularity
    FROM albums_data a
    JOIN tracks_data t ON a.track_id = t.id
    JOIN artist_data ar ON a.artist_id = ar.id
    """
    df_pop = get_data(query_pop)

    correlation = df_pop.corr()
    print("Correlation:", correlation)

    fig, ax = plt.subplots()
    sns.scatterplot(x='artist_popularity', y='album_popularity', data=df_pop, ax=ax)
    ax.set_title("Artist vs Album Popularity")

    return df_pop, correlation, fig

if __name__ == "__main__":
    df_pop, corr, fig = analyze_popularity()
    plt.show()
    fig.savefig("artist_vs_album_popularity.png")