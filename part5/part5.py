import streamlit as st
from part1_functions import (
    load_data,
    plot_popularity,
    plot_followers,
    get_correlation,
    plot_popularity_vs_followers,
    get_overperformers_and_legacy,
    plot_overperformers_legacy
)
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
""", unsafe_allow_html=True)
st.markdown("""
    <style>
    .stApp { background-color: #191414; color: white; }
    [data-testid="stMetric"] { background-color: #1DB954; border-radius: 10px; padding: 10px; }
    [data-testid="stMetricLabel"] { color: white !important; }
    [data-testid="stMetricValue"] { color: white !important; }
    </style>
""", unsafe_allow_html=True)

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

    st.divider()
    st.subheader("Popularity vs Followers")

    # Create two columns for the metric and the plot
    col1, spacer, col2 = st.columns([1, 0.2, 2])
    with col1:
        st.metric(
            "Correlation between popularity and log followers",
            round(correlation, 3)
        )

        st.divider()
#        st.write("\n \n") # Add some vertical space

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

    # Style the over-performers table
    styled_over = (
        over_performers
        .reset_index(drop=True)
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

    # Style the legacy artists table
    styled_legacy = (
        legacy_artists
        .reset_index(drop=True)
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
        st.pyplot(plot_overperformers_legacy(df))

    with right_col:
        st.subheader("Top 10 Over-performers")

        st.markdown(
            f"""
            <div style="height:200px; overflow-y:auto;">
                {styled_over.to_html()}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        st.subheader("Top 10 Legacy Artists")

        st.markdown(
            f"""
            <div style="height:200px; overflow-y:auto;">
                {styled_legacy.to_html()}
            </div>
            """,
            unsafe_allow_html=True
        )