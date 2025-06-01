import pandas as pd
import numpy as np
import argparse

def analyze_book_prices(csv_file):
    try:
        # Load the dataset
        df = pd.read_csv(csv_file)

        # Print the first 5 rows of the DataFrame
        print("First 5 rows of the dataset:")
        print(df.head())

        # Print the column names
        print("\nColumn names:")
        print(df.columns)

        print("\nSuccessfully loaded dataset. You can now start exploring and cleaning the data!")

    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        print("Please make sure the dataset file exists in the specified path.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description='Analyze book price data from a CSV file.')
    parser.add_argument('csv_file', type=str, help='Path to the CSV file to analyze')
    args = parser.parse_args()
    
    analyze_book_prices(args.csv_file)

if __name__ == "__main__":
    main()
