import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from db_utils import get_data

def analyze_collaborations():
    """Analyze whether collaborations are more popular than solo tracks.
    Returns (df_collab, avg_popularity, figure)."""
    print("--- Question: Are collaborations more popular? ---")
    
    query_collab = """
    SELECT 
        t.track_popularity,
        a.artist_0,
        a.artist_1
    FROM tracks_data t
    JOIN albums_data a ON t.id = a.track_id
    """
    
    df_collab = get_data(query_collab)

    df_collab['is_collab'] = df_collab['artist_1'].notna() & (df_collab['artist_1'] != '')
    df_collab['is_collab'] = df_collab['is_collab'].astype(int)
    
    avg_popularity = df_collab.groupby('is_collab').agg(
        average_popularity=('track_popularity', 'mean'),
        total_tracks=('track_popularity', 'count')
    ).reset_index()
    
    avg_popularity['Track Type'] = avg_popularity['is_collab'].map({0: 'Solo Track', 1: 'Collaboration'})
    
    print("\nAverage Popularity Comparison:")
    print(avg_popularity[['Track Type', 'average_popularity', 'total_tracks']].to_string(index=False))
    
    # --- Visualization ---
    fig, ax = plt.subplots(figsize=(7, 5))

    # Background
    fig.patch.set_facecolor("#191414")
    ax.set_facecolor("#191414")

    sns.barplot(
        data=avg_popularity, 
        x='Track Type', 
        y='average_popularity', 
        palette=['#1DB954', '#1ed760'],
        ax=ax
    )
    ax.set_title("Popularity of Solo Tracks vs. Collaborations", color='white')
    ax.set_ylabel("Average Popularity", color='white')
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    
    for index, row in avg_popularity.iterrows():
        ax.text(index, row.average_popularity + 0.5, round(row.average_popularity, 2), color='white', ha="center")

    return df_collab, avg_popularity, fig
        
if __name__ == "__main__":
    df_collab, avg_popularity, fig = analyze_collaborations()
    plt.show()
    fig.savefig("collaborations_popularity_comparison.png")
