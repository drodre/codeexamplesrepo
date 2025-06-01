import pandas as pd
import numpy as np
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description="Analyze book prices from a CSV file.")
parser.add_argument('--dataset_path', type=str, default='book_prices.csv',
                    help="Path to the dataset CSV file (default: 'book_prices.csv')")

args = parser.parse_args()
dataset_path = args.dataset_path

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

    # Identify empty rows (all values are NaN)
        empty_rows = df.isnull().all(axis=1)
        num_empty_rows = empty_rows.sum()

        print(f"\nNumber of empty rows (all values NaN): {num_empty_rows}")
        if num_empty_rows > 0:
            print("Indices of empty rows:")
            print(df[empty_rows].index.tolist())

        # Identify duplicate rows based on 'codigo_isbn'
        # The `keep=False` argument marks all duplicates, including the first occurrence.
        # To only get subsequent duplicates, we can use `keep='first'` and then filter.
        duplicates_isbn = df[df.duplicated(subset=['codigo_isbn'], keep=False)]
        # To count only the *extra* copies, not all items that are part of a duplicate set:
        num_duplicate_isbn_entries = df.duplicated(subset=['codigo_isbn'], keep='first').sum()

        print(f"\nNumber of duplicate entries based on 'codigo_isbn' (excluding first occurrences): {num_duplicate_isbn_entries}")
        if num_duplicate_isbn_entries > 0:
            print("Duplicate rows (based on 'codigo_isbn', showing all occurrences of duplicates):")
            # Displaying rows that are marked as duplicates (all occurrences)
            print(duplicates_isbn.sort_values(by='codigo_isbn'))

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
