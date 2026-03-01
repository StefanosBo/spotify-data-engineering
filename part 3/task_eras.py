import pandas as pd
from db_utils import get_data

def categorize_eras():
    query = "SELECT * FROM albums_data"
    df_albums = get_data(query)
    
    if 'release_date' in df_albums.columns:
        df_albums['release_date'] = pd.to_datetime(df_albums['release_date'])
        
        def get_era(year):
            if pd.isna(year):
                return "Unknown"
            return f"{str(int(year))[:3]}0s"
        
        df_albums['era'] = df_albums['release_date'].dt.year.apply(get_era)
        
        print("--- Album Counts by Era ---")
        print(df_albums['era'].value_counts().sort_index())
    else:
        print("Please verify the exact name of the date column in albums_data.")

if __name__ == "__main__":
    categorize_eras()