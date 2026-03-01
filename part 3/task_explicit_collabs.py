import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from db_utils import get_data

def analyze_explicit_tracks():
    print("--- Are explicit tracks more popular? ---")
    query_explicit = """
    SELECT 
        explicit, 
        track_popularity 
    FROM tracks_data
    """
    

    df_explicit = get_data(query_explicit)
    
    avg_popularity = df_explicit.groupby('explicit')['track_popularity'].mean().reset_index()
    print("Average Popularity by Explicit Status:")
    print(avg_popularity.to_string(index=False))
    
    plt.figure(figsize=(6, 4))
    sns.barplot(data=df_explicit, x='explicit', y='track_popularity', errorbar=None)
    plt.title("Average Popularity: Explicit vs. Clean Tracks")
    plt.xlabel("Is Explicit (1 = Yes, 0 = No)")
    plt.ylabel("Average Popularity")
    plt.show()
    plt.savefig("explicit_vs_popularity.png")
    
    
    print("\n--- Which artists have the highest proportion of explicit tracks? ---")
    query_proportion = """
        SELECT 
            ar.name, 
            t.explicit 
        FROM artist_data ar
        JOIN albums_data al ON ar.id = al.artist_id
        JOIN tracks_data t ON al.track_id = t.id
    """
    
    df_prop = get_data(query_proportion)
    df_prop['explicit'] = df_prop['explicit'].astype(str).str.lower().map({'true': 1, 'false': 0})
    
    artist_stats = df_prop.groupby('name').agg(
        total_tracks=('explicit', 'count'),
        explicit_tracks=('explicit', 'sum')
    ).reset_index()
    print(artist_stats.head())
    artist_stats['explicit_proportion'] = artist_stats['explicit_tracks'] / artist_stats['total_tracks']
    
    artist_stats_filtered = artist_stats[artist_stats['total_tracks'] >= 5]
    
    top_explicit_artists = artist_stats_filtered.sort_values(by='explicit_proportion', ascending=False).head(10)
    
    print("Top 10 Artists with the Highest Proportion of Explicit Tracks (min. 5 tracks):")
    print(top_explicit_artists[['name', 'explicit_proportion', 'total_tracks']].to_string(index=False))


if __name__ == "__main__":
    analyze_explicit_tracks()