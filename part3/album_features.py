import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from db_utils import get_data

def analyze_album_consistency(album_name="The Dark Side Of The Moon"):
    """Analyze feature consistency for tracks on an album.
    Returns (DataFrame, figure) so the dashboard can display them."""
    query = f"""
        SELECT 
            a.album_name,
            a.track_name,
            f.danceability,
            f.loudness
        FROM albums_data a
        JOIN features_data f ON a.track_id = f.id
        WHERE a.album_name = '{album_name}'
    """

    df_album = get_data(query)
    print(df_album.head(20))
    
    print(f"--- Analysis for Album: {album_name} ---")
    print(df_album.describe())
    
    # Visualization
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df_album[['danceability', 'loudness']], ax=ax)
    ax.set_title(f"Consistency of Features: {album_name}")

    return df_album, fig

if __name__ == "__main__":
    df, fig = analyze_album_consistency()
    plt.show()
    fig.savefig(f"The Dark Side Of The Moon_consistency.png")
