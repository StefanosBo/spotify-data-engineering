import streamlit as st
from part1_functions import (
    load_data,
    plot_popularity,
    plot_followers,
    get_correlation,
    plot_popularity_vs_followers,
    get_overperformers_and_legacy,
    plot_overperformers_legacy,
    get_top_genres,
    plot_top_genres,
    get_artists_by_genre,
    plot_artists_by_genre,
    get_num_genres_summary,
    plot_num_genres_vs_popularity,
    plot_num_genres_vs_followers,
    plot_follower_groups_vs_popularity
)

# debugging
import part1_functions
print(dir(part1_functions))
df = load_data()

# Page config
st.set_page_config(page_title="Spotify Dashboard", page_icon="🎵", layout="wide")

# Spotify styling
st.markdown("""
    <style>
    .stApp { background-color: #191414; color: white; }
    </style>
""", unsafe_allow_html=True) # Set dark background for the whole app
st.markdown("""
    <style>
    .stApp { background-color: #191414; color: white; }
    [data-testid="stMetric"] { background-color: #1DB954; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricLabel"] { color: white !important; }
    [data-testid="stMetricValue"] { color: white !important; }
    </style>
""", unsafe_allow_html=True) # Add Spotify green background to metrics and ensure text is white

df = load_data()

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigate",
    ["Overview", "Popularity Analysis", "Genre Explorer", "Artist Search"]
)

# Overview page
if page == "Overview":
    st.title("🎵 Spotify Artist Dashboard")
    st.write("General statistics of the dataset")

elif page == "Popularity Analysis":
    st.title("📈 Popularity Analysis")

elif page == "Genre Explorer":
    st.title("🎸 Genre Explorer")

elif page == "Artist Search":
    st.title("🔍 Artist Search")

if page == "Overview":

    # Numerical stats in 3 columns
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Artists", df["name"].nunique())
    col2.metric("Average Popularity", round(df["artist_popularity"].mean(), 1))
    col3.metric("Most Followed Artist", df.loc[df["followers"].idxmax(), "name"])

    st.divider()

    # Plots
    col1, col2 = st.columns(2)

    with col1:
        st.pyplot(plot_popularity(df))

    with col2:    
        st.pyplot(plot_followers(df))

# Popularity analysis page
elif page == "Popularity Analysis":

    correlation = get_correlation(df)

    st.divider() # Divider for better separation of sections
    st.subheader("Popularity vs Followers")

    # Create two columns for the metric and the plot
    col1, spacer, col2 = st.columns([1, 0.2, 2])
    with col1:
        st.metric(
            "Correlation between popularity and log followers",
            round(correlation, 3)
        )

        st.write("\n \n") # Add some vertical space

        # Add an insight box to fill the space
        st.markdown(
            """
            **Insight 💡**  
            There is a strong positive relationship between followers and popularity.  
            However, some artists significantly over- or under-perform relative to their audience size.
            """
        )
        
    # Plot the scatter plot in the second column
    with col2:
        st.pyplot(plot_popularity_vs_followers(df))

    # Add a divider and section for over-performers and legacy artists
    st.divider()
    st.subheader("Over-performers and Legacy Artists")
    
    # Get the over-performers and legacy artists
    over_performers, legacy_artists = get_overperformers_and_legacy(df)

    # Prepare dataframe first
    over_df = over_performers.reset_index(drop=True)
    over_df.index += 1
    over_df.index.name = "#"

    # Style the over-performers table
    styled_over = (
        over_df
        [["name", "artist_popularity", "followers"]]
        .rename(columns={
            "artist_popularity": "Popularity",
            "followers": "Followers"
        }) # Format the table with renamed columns and only relevant info
        .style
        .set_properties(**{
            "background-color": "#191414",
            "color": "white",
            "border-color": "#1DB954"
        }) # Set dark background and green borders for the table
        .set_table_styles([
            {"selector": "th", "props": [("background-color", "#1DB954"), ("color", "white")]},
            {"selector": "td", "props": [("border", "1px solid #1DB954")]}
        ]) # Style the header and cells with Spotify green and white text
    )

    # Prepare dataframe first
    legacy_df = legacy_artists.reset_index(drop=True)
    legacy_df.index += 1
    legacy_df.index.name = "#"

    # Style the legacy artists table
    styled_legacy = (
        legacy_df
        [["name", "artist_popularity", "followers"]]
        .rename(columns={
            "artist_popularity": "Popularity",
            "followers": "Followers"
        })
        .style
        .set_properties(**{
            "background-color": "#191414",
            "color": "white",
            "border-color": "#1DB954"
        })
        .set_table_styles([
            {"selector": "th", "props": [("background-color", "#1DB954"), ("color", "white")]},
            {"selector": "td", "props": [("border", "1px solid #1DB954")]}
        ])
    )

    # Display the plot and tables side by side
    left_col, right_col = st.columns([1.8, 1])

    with left_col:
        st.subheader("Model View")
        st.pyplot(plot_overperformers_legacy(df)) # Plot the over-performers and legacy artists in the left column

    with right_col:
        st.subheader("Top 10 Over-performers")

        st.markdown(
            f'<div style="height:200px; overflow-y:auto;">{styled_over.to_html()}</div>',
            unsafe_allow_html=True
        )   # Display the over-performers table in a scrollable div

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        st.subheader("Top 10 Legacy Artists")

        # scrollable table for legacy artists
        st.markdown(
            f'<div style="height:200px; overflow-y:auto;">{styled_legacy.to_html()}</div>',
            unsafe_allow_html=True
        ) 

    st.divider()

    # Add a section for genre breadth analysis
    st.subheader("Genre Breadth Analysis")

    genre_summary = get_num_genres_summary(df)

    col1, col2, col3 = st.columns(3) # Create three columns for the summary metrics

    # Display the summary metrics for number of genres and correlations
    with col1:
        st.metric("Average # of Genres", round(genre_summary["mean_num_genres"], 2))

    with col2:
        st.metric("Correlation with Popularity", round(genre_summary["corr_popularity"], 3))

    with col3:
        st.metric("Correlation with Followers", round(genre_summary["corr_followers"], 3))

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    col4, col5 = st.columns(2)

    # Plot the number of genres vs popularity 
    with col4:
        st.pyplot(plot_num_genres_vs_popularity(df))

    # Plot the number of genres vs followers
    with col5:
        st.pyplot(plot_num_genres_vs_followers(df))

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

    st.pyplot(plot_follower_groups_vs_popularity(df))

# Genre explorer page
elif page == "Genre Explorer":

    # Sidebar input for genre
    genre_input = st.sidebar.text_input("Enter a genre", value="pop")

    # Get top genres for display
    st.subheader("Most Common Genres")
    st.pyplot(plot_top_genres(df))

    col1, spacer, col2 = st.columns([1.3, 0.15, 1]) # spacer used to adjust column widths for better balance

    # the plot of top artists by genre  
    with col1:
        st.subheader(f"Top Artists in '{genre_input}'")
        st.pyplot(plot_artists_by_genre(df, genre_input))

    # the table of top artists by genre
    with col2:
        genre_table = get_artists_by_genre(df, genre_input)

        if not genre_table.empty:
            genre_table = genre_table.reset_index(drop=True)
            genre_table.index = genre_table.index + 1
            genre_table.index.name = "#"

            styled_genre = (
                genre_table[["name", "artist_popularity", "followers"]]
                .rename(columns={
                    "artist_popularity": "Popularity",
                    "followers": "Followers"
                })
                .style
                .set_properties(**{
                    "background-color": "#191414",
                    "color": "white",
                    "border-color": "#1DB954"
                })
                .set_table_styles([
                    {"selector": "th", "props": [("background-color", "#1DB954"), ("color", "white")]},
                    {"selector": "td", "props": [("border", "1px solid #1DB954")]},
                    {"selector": "table", "props": [("border-collapse", "collapse"), ("width", "100%")]}
                ])
            )

            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True) # Add some vertical space
            st.markdown(styled_genre.to_html(), unsafe_allow_html=True)
        else:
            st.warning("No artists found for this genre.")
