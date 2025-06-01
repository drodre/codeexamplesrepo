import pandas as pd
import numpy as np

# Path to your dataset
# Make sure to replace 'book_prices.csv' with the actual name of your dataset file
# and ensure the file is in the same directory as this script,
# or provide the full path to the file.
dataset_path = 'book_prices.csv'

try:
    # Load the dataset
    df = pd.read_csv(dataset_path)

    # Print the first 5 rows of the DataFrame
    print("First 5 rows of the dataset:")
    print(df.head())

    # Print the column names
    print("\nColumn names:")
    print(df.columns)

    print("\nSuccessfully loaded dataset. You can now start exploring and cleaning the data!")

except FileNotFoundError:
    print(f"Error: The file '{dataset_path}' was not found.")
    print("Please make sure the dataset file exists in the specified path.")
except Exception as e:
    print(f"An error occurred: {e}")
