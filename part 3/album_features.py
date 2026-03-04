import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from db_utils import get_data

def analyze_album_consistency(album_name="The Dark Side Of The Moon"):
    # SQL query to join albums_data and features_data on track_id
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
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=df_album[['danceability', 'loudness']])
    plt.title(f"Consistency of Features: {album_name}")
    plt.show()
    plt.savefig(f"{album_name}_consistency.png")

if __name__ == "__main__":
    analyze_album_consistency()