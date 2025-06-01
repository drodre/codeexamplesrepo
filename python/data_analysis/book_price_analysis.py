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

        # Identify empty rows (all values are NaN)
        empty_rows = df.isnull().all(axis=1)
        num_empty_rows = empty_rows.sum()

        print(f"\nNumber of empty rows (all values NaN): {num_empty_rows}")
        if num_empty_rows > 0:
            print("Indices of empty rows:")
            print(df[empty_rows].index.tolist())

        # Identify duplicate rows based on 'codigo_isbn'
        # The `keep=False` argument marks all duplicates, including the first occurrence.
        duplicates_isbn = df[df.duplicated(subset=['codigo_isbn'], keep=False)]
        # To count only the *extra* copies, not all items that are part of a duplicate set:
        num_duplicate_isbn_entries = df.duplicated(subset=['codigo_isbn'], keep='first').sum()

        print(f"\nNumber of duplicate entries based on 'codigo_isbn' (excluding first occurrences): {num_duplicate_isbn_entries}")
        if num_duplicate_isbn_entries > 0:
            print("Duplicate rows (based on 'codigo_isbn', showing all occurrences of duplicates):")
            # Displaying rows that are marked as duplicates (all occurrences)
            print(duplicates_isbn.sort_values(by='codigo_isbn'))

        # --- Processing 'fecha_publicacion' ---
        print("\n--- Processing 'fecha_publicacion' ---")
        df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
        num_nat = df['fecha_publicacion'].isnull().sum()
        print(f"Number of rows with unparseable dates (NaT): {num_nat}")
        print(f"Data type of 'fecha_publicacion' after conversion: {df['fecha_publicacion'].dtype}")
        if len(df) - num_nat > 0: # Check if there are any valid dates
            print("First 5 values of 'fecha_publicacion' after conversion:")
            print(df['fecha_publicacion'].head())
        else:
            print("No valid dates found in 'fecha_publicacion' after conversion.")

        # --- Validating 'nro_paginas' ---
        print("\n--- Validating 'nro_paginas' ---")
        original_nans_nro_paginas = df['nro_paginas'].isnull().sum()
        df['nro_paginas'] = pd.to_numeric(df['nro_paginas'], errors='coerce')
        coerced_nans_nro_paginas = df['nro_paginas'].isnull().sum() - original_nans_nro_paginas
        print(f"Number of rows with non-numeric 'nro_paginas' (coerced to NaN): {coerced_nans_nro_paginas}")
        print(f"Total NaN values in 'nro_paginas' after conversion: {df['nro_paginas'].isnull().sum()}")
        print(f"Data type of 'nro_paginas' after conversion: {df['nro_paginas'].dtype}")
        print("Descriptive statistics for 'nro_paginas':")
        print(df['nro_paginas'].describe())

        # Impute NaNs in nro_paginas with 0
        nan_count_before_imputation = df['nro_paginas'].isnull().sum()
        if nan_count_before_imputation > 0:
            df['nro_paginas'].fillna(0, inplace=True)
            print(f"Imputed {nan_count_before_imputation} NaN values in 'nro_paginas' with 0.")
            # Display descriptive statistics again to see the impact of imputation
            print("Descriptive statistics for 'nro_paginas' after imputation:")
            print(df['nro_paginas'].describe())
        else:
            print("No NaN values to impute in 'nro_paginas'.")

        print("\nPotential outliers in 'nro_paginas' (e.g., 1 page books):")
        one_page_books = df[df['nro_paginas'] == 1]
        if not one_page_books.empty:
            print(one_page_books.head())
        else:
            print("No books found with exactly 1 page.")

        # --- Validating 'precio' ---
        print("\n--- Validating 'precio' ---")
        original_nans_precio = df['precio'].isnull().sum()
        df['precio'] = pd.to_numeric(df['precio'], errors='coerce')
        coerced_nans_precio = df['precio'].isnull().sum() - original_nans_precio
        print(f"Number of rows with non-numeric 'precio' (coerced to NaN): {coerced_nans_precio}")
        print(f"Total NaN values in 'precio' after conversion: {df['precio'].isnull().sum()}")
        print(f"Data type of 'precio' after conversion: {df['precio'].dtype}")
        print("Descriptive statistics for 'precio':")
        print(df['precio'].describe())

        print("\nPotential outliers in 'precio' (max price books):")
        max_price = df['precio'].max()
        if pd.notna(max_price): # Check if max_price is not NaN (i.e., if 'precio' column is not all NaN)
            max_price_books = df[df['precio'] == max_price]
            if not max_price_books.empty:
                print(max_price_books)
            else:
                # This case should ideally not be reached if max_price is not NaN and describe() worked.
                print("No books found at the maximum price (this is unexpected if max price was calculated).")
        else:
            print("Cannot determine maximum price as 'precio' column might be all NaN or empty.")

        # --- Currency Conversion for 'precio' (ARS to EUR) ---
        print("\n--- Currency Conversion 'precio' ARS to EUR ---")
        ars_to_eur_rate = 1340  # 1 EUR = 1340 ARS
        df['precio_eur'] = (df['precio'] / ars_to_eur_rate).round(2)

        print(f"Converted 'precio' to 'precio_eur' using rate: 1 EUR = {ars_to_eur_rate} ARS.")
        print("First 5 rows with ARS and EUR prices:")
        print(df[['titulo', 'precio', 'precio_eur']].head())

        print("\nDescriptive statistics for 'precio_eur':")
        print(df['precio_eur'].describe())

        print("\nSuccessfully processed dataset. Basic checks for empty rows and duplicates are complete.")

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
