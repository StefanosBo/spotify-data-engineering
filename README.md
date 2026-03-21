# Spotify Data Engineering Project

## Contents
- Project Overview and dependencies
- Part 1: Artist Analysis
- Part 3: Database Analysis
- Part 4: Data Wrangling 

## Project Overview
This project performs exploratory data analysis on Spotify data to uncover insights about artists, albums, tracks, and their popularity metrics. It consists of multiple parts analyzing different aspects of the data.

## Dependencies for the Whole Project
- pandas
- matplotlib
- numpy
- statsmodels
- seaborn
- sqlite3 (built-in)

Install all dependencies (PowerShell or cmd):
```powershell
py -m pip install pandas matplotlib numpy statsmodels seaborn
```

## Data Expectations for the Whole Project
- Part 1: CSV file `data/artist_data.csv` with artist info (name, followers, popularity, genres)
- Part 3: SQLite database `part3/spotify_database.db` with tables for albums, tracks, artists, features
- Common filters: positive followers/popularity, exclude "Various Artists"

---

## Part 1: Artist Popularity & Followers Analysis (part1/intro.py)

### Overview
This script explores Spotify artist data from `data/artist_data.csv` and performs:
- data cleaning and filtering
- descriptive stats and missing-value checks
- top artists by popularity and followers
- plots (bar charts and scatter with regression)
- correlation and OLS regression between popularity and log followers
- identification of over-performers and legacy artists via residuals
- genre breakdown and interactive genre-based ranking

### How to run
```powershell
py part1\intro.py
```

### Data expectations
- Input file: `data/artist_data.csv`
- Filtering:
  - `followers` > 0
  - `artist_popularity` > 0
  - `name` != "Various Artists"

### Outputs generated
- console logs of data schema, data shape, missing values, top artists
- top 10 charts by popularity and followers
- correlation value and linear regression summary
- scatter plot with regression line
- over-performers and legacy artists printed
- top 15 genres by frequency printed
- interactive genre `TextBox` plot to inspect popularity leaderboard

---

## Part 3: Spotify Database Analysis (part3/)

### Overview
This part analyzes Spotify data stored in a SQLite database (`spotify_database.db`) and includes scripts for:
- Album feature consistency analysis (danceability, loudness)
- Collaboration popularity comparison (solo vs collab tracks)
- Artist vs album popularity correlation
- Album era categorization by decades
- Explicit tracks popularity and artist explicit proportions

### How to run
Each script can be run individually:
```powershell
py part3\album_features.py
py part3\collaborations.py
py part3\dbutils.py
py part3\popularity.py
py part3\task_eras.py
py part3\task_explicit_collabs.py
```

### Data expectations
- SQLite database: `part3/spotify_database.db` # COME BACK: we might want to also use data from the data file for consistency
- Tables: `albums_data`, `tracks_data`, `artist_data`, `features_data`
- Key columns: track_id, album_name, track_name, danceability, loudness, track_popularity, artist_0, artist_1, artist_popularity, album_popularity, release_date, explicit, etc.

### Outputs generated
- Console prints of analyses, stats, top lists
- PNG plots saved in part3/ (e.g., consistency plots, popularity comparisons)

---

## Part 4: Spotify Data Wrangling and Time Analysis (part4/spotify_wrangle.py)

### Overview
This script performs data wrangling on Spotify data from the SQLite database, including:
- Outlier detection for track popularity, energy, and artist popularity using IQR
- Data cleaning (remove invalid IDs, duplicates, negative durations)
- Date processing and year extraction from release dates
- Time-series analysis: plotting average energy, danceability, valence, and tempo over years

### How to run
```powershell
py part4\spotify_wrangle.py
```

### Data expectations
- SQLite database: `data/spotify_database.db` (note: different path from part3)
- Same tables as part3: `tracks_data`, `features_data`, `artist_data`, `albums_data`
- Key columns: id, track_id, track_popularity, energy, artist_popularity, release_date, duration_ms, etc.

### Outputs generated
- Console prints of outlier counts
- Plots: Energy/Danceability/Valence over time, Tempo over time

---

# Part 5: 

