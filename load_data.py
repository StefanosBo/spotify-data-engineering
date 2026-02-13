import pandas as pd

df = pd.read_csv("data/artist_data.csv")
print(df.head())
print("Rows, Cols:", df.shape)