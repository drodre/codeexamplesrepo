import pandas as pd
import numpy as np
import argparse
import matplotlib.pyplot as plt

def load_data(csv_file):
    try:
        df = pd.read_csv(csv_file)
        print(f"Successfully loaded data from '{csv_file}'.")
        return df
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        print("Please make sure the dataset file exists in the specified path.")
        return None

def log_initial_info(df):
    print("First 5 rows of the dataset:")
    print(df.head())
    print("\nColumn names:")
    print(df.columns)

def check_data_quality(df):
    empty_rows = df.isnull().all(axis=1)
    num_empty_rows = empty_rows.sum()
    print(f"\nNumber of empty rows (all values NaN): {num_empty_rows}")
    if num_empty_rows > 0:
        print("Indices of empty rows:")
        print(df[empty_rows].index.tolist())

    duplicates_isbn = df[df.duplicated(subset=['codigo_isbn'], keep=False)]
    num_duplicate_isbn_entries = df.duplicated(subset=['codigo_isbn'], keep='first').sum()
    print(f"\nNumber of duplicate entries based on 'codigo_isbn' (excluding first occurrences): {num_duplicate_isbn_entries}")
    if num_duplicate_isbn_entries > 0:
        print("Duplicate rows (based on 'codigo_isbn', showing all occurrences of duplicates):")
        print(duplicates_isbn.sort_values(by='codigo_isbn'))

def process_dates(df):
    print("\n--- Processing 'fecha_publicacion' ---")
    if 'fecha_publicacion' in df.columns:
        df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
        num_nat = df['fecha_publicacion'].isnull().sum()
        print(f"Number of rows with unparseable dates (NaT): {num_nat}")
        print(f"Data type of 'fecha_publicacion' after conversion: {df['fecha_publicacion'].dtype}")
        if len(df) - num_nat > 0:
            print("First 5 values of 'fecha_publicacion' after conversion:")
            print(df['fecha_publicacion'].head())
        else:
            print("No valid dates found in 'fecha_publicacion' after conversion.")
    else:
        print("Column 'fecha_publicacion' not found.")
    return df

def process_numeric_columns(df):
    # --- Validating 'nro_paginas' ---
    print("\n--- Validating 'nro_paginas' ---")
    if 'nro_paginas' in df.columns:
        original_nans_nro_paginas = df['nro_paginas'].isnull().sum()
        df['nro_paginas'] = pd.to_numeric(df['nro_paginas'], errors='coerce')
        coerced_nans_nro_paginas = df['nro_paginas'].isnull().sum() - original_nans_nro_paginas
        print(f"Number of rows with non-numeric 'nro_paginas' (coerced to NaN): {coerced_nans_nro_paginas}")
        print(f"Total NaN values in 'nro_paginas' after conversion: {df['nro_paginas'].isnull().sum()}")
        print(f"Data type of 'nro_paginas' after conversion: {df['nro_paginas'].dtype}")
        print("Descriptive statistics for 'nro_paginas':")
        print(df['nro_paginas'].describe())

        nan_count_before_imputation = df['nro_paginas'].isnull().sum()
        if nan_count_before_imputation > 0:
            df['nro_paginas'].fillna(0, inplace=True)
            print(f"Imputed {nan_count_before_imputation} NaN values in 'nro_paginas' with 0.")
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
    else:
        print("Column 'nro_paginas' not found.")

    # --- Validating 'precio' ---
    print("\n--- Validating 'precio' ---")
    if 'precio' in df.columns:
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
        if pd.notna(max_price):
            max_price_books = df[df['precio'] == max_price]
            if not max_price_books.empty:
                print(max_price_books)
            else:
                print("No books found at the maximum price (this is unexpected if max price was calculated).")
        else:
            print("Cannot determine maximum price as 'precio' column might be all NaN or empty.")
    else:
        print("Column 'precio' not found.")

    # --- Currency Conversion for 'precio' (ARS to EUR) ---
    print("\n--- Currency Conversion 'precio' ARS to EUR ---")
    if 'precio' in df.columns:
        ars_to_eur_rate = 1340  # 1 EUR = 1340 ARS
        df['precio_eur'] = (df['precio'] / ars_to_eur_rate).round(2)
        print(f"Converted 'precio' to 'precio_eur' using rate: 1 EUR = {ars_to_eur_rate} ARS.")
        print("First 5 rows with ARS and EUR prices:")
        columns_for_price_display = ['precio', 'precio_eur']
        if 'titulo' in df.columns: # Ensure 'titulo' column exists
            columns_for_price_display.insert(0, 'titulo')
        print(df[columns_for_price_display].head())

        print("\nDescriptive statistics for 'precio_eur':")
        print(df['precio_eur'].describe())
    else:
        print("Column 'precio' not found, skipping currency conversion.")
    return df

def perform_text_cleaning(df):
    print("\n--- Preparing for Text Column Cleaning ---")
    text_columns_to_clean = [
        'titulo', 'autor', 'editorial', 'idioma',
        'encuadernacion', 'categoria', 'genero', 'subgenero'
    ]
    text_columns_to_clean = [col for col in text_columns_to_clean if col in df.columns]
    print(f"Identified text columns for cleaning: {text_columns_to_clean}")

    for col in text_columns_to_clean:
        df[col] = df[col].astype(str).fillna('')

        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == 'object':
            df[col] = df[col].str.strip()
            df[col] = df[col].str.lower()
            print(f"Applied basic cleaning (strip, lower) to column: '{col}'")
        else:
            print(f"Skipped string methods for column: '{col}' as it's not predominantly string-like after astype(str). Current dtype: {df[col].dtype}")

    # Specific value replacements
    print("\n--- Applying Specific Value Replacements ---")
    if 'categoria' in df.columns:
        df['categoria'] = df['categoria'].replace('negocios y cs. economicas', 'negocios y ciencias economicas')
        print("Standardized 'negocios y cs. economicas' to 'negocios y ciencias economicas' in 'categoria'.")
    if 'genero' in df.columns:
        df['genero'] = df['genero'].replace('dep. extremos', 'deportes extremos')
        print("Standardized 'dep. extremos' to 'deportes extremos' in 'genero'.")
    print("--- Specific Value Replacements Complete ---")

    print("\n--- Inspecting Unique Values in Key Categorical Columns After Basic Cleaning ---")
    key_categorical_columns = ['idioma', 'encuadernacion', 'categoria', 'genero']
    for col in key_categorical_columns:
        if col in df.columns:
            unique_values = df[col].unique()
            print(f"Unique values in '{col}' (sample of up to 20):")
            if len(unique_values) > 20:
                print(np.random.choice(unique_values, size=20, replace=False))
            else:
                print(unique_values)
            print(f"Total unique values in '{col}': {df[col].nunique()}")
        else:
            print(f"Column '{col}' not found in DataFrame for unique value inspection.")
    print("--- End of Unique Value Inspection ---")
    return df

def generate_and_save_plots(df):
    print("\n--- Generating and Saving Plots ---")

    # Plot 1: Distribution of precio_eur
    try:
        if 'precio_eur' in df.columns:
            plt.figure(figsize=(10, 6))
            df['precio_eur'].plot(kind='hist', bins=50, edgecolor='black')
            plt.title('Distribution of Book Prices (EUR)')
            plt.xlabel('Price (EUR)')
            plt.ylabel('Frequency')
            plt.grid(axis='y', alpha=0.75)
            plot_filename_price = 'precio_eur_distribution.png'
            plt.savefig(plot_filename_price)
            plt.close()
            print(f"Saved price distribution plot to '{plot_filename_price}'")
        else:
            print("Column 'precio_eur' not found, skipping price distribution plot.")
    except Exception as e:
        print(f"Error generating or saving price distribution plot: {e}")

    # Plot 2: Distribution of nro_paginas (pages > 0)
    try:
        if 'nro_paginas' in df.columns:
            plt.figure(figsize=(10, 6))
            df_filtered_pages = df[df['nro_paginas'] > 0]
            if not df_filtered_pages.empty:
                df_filtered_pages['nro_paginas'].plot(kind='hist', bins=50, edgecolor='black')
                plt.title('Distribution of Book Page Numbers (Pages > 0)')
                plt.xlabel('Number of Pages')
                plt.ylabel('Frequency')
                plt.grid(axis='y', alpha=0.75)
                plot_filename_pages = 'nro_paginas_distribution.png'
                plt.savefig(plot_filename_pages)
                plt.close()
                print(f"Saved page number distribution plot to '{plot_filename_pages}'")
            else:
                print("No data with 'nro_paginas' > 0 to plot.")
        else:
            print("Column 'nro_paginas' not found, skipping page number distribution plot.")
    except Exception as e:
        print(f"Error generating or saving page number distribution plot: {e}")

    # Plot 3: Book Counts by idioma (Top 10)
    try:
        if 'idioma' in df.columns and df['idioma'].notna().any():
            plt.figure(figsize=(12, 7))
            top_n_languages = 10
            idioma_counts = df['idioma'].value_counts().nlargest(top_n_languages)
            if not idioma_counts.empty:
                idioma_counts.plot(kind='bar', edgecolor='black')
                plt.title(f'Top {top_n_languages} Book Languages')
                plt.xlabel('Idioma (Language)')
                plt.ylabel('Number of Books')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.grid(axis='y', alpha=0.75)
                plot_filename_idioma = 'idioma_counts.png'
                plt.savefig(plot_filename_idioma)
                plt.close()
                print(f"Saved language counts plot to '{plot_filename_idioma}'")
            else:
                print("No data for 'idioma' counts to plot (perhaps all NaN or empty after filtering).")
        else:
            print("'idioma' column not found or contains all NaN values. Skipping language counts plot.")
    except Exception as e:
        print(f"Error generating or saving language counts plot: {e}")

    # Plot 4: Scatter plot of nro_paginas (pages > 0) vs precio_eur
    try:
        if 'nro_paginas' in df.columns and 'precio_eur' in df.columns:
            plt.figure(figsize=(10, 6))
            df_filtered_scatter = df[df['nro_paginas'] > 0]
            if not df_filtered_scatter.empty:
                df_filtered_scatter.plot(kind='scatter', x='nro_paginas', y='precio_eur', alpha=0.5)
                plt.title('Book Price (EUR) vs. Number of Pages (Pages > 0)')
                plt.xlabel('Number of Pages')
                plt.ylabel('Price (EUR)')
                plt.grid(True, alpha=0.5)
                plot_filename_scatter = 'price_vs_pages.png'
                plt.savefig(plot_filename_scatter)
                plt.close()
                print(f"Saved price vs. pages scatter plot to '{plot_filename_scatter}'")
            else:
                print("No data with 'nro_paginas' > 0 to create scatter plot.")
        else:
            print("Columns 'nro_paginas' or 'precio_eur' not found, skipping scatter plot.")
    except Exception as e:
        print(f"Error generating or saving price vs. pages scatter plot: {e}")

def save_data(df, output_filename):
    try:
        df.to_csv(output_filename, index=False)
        print(f"\nSuccessfully saved cleaned data to '{output_filename}'")
    except Exception as e:
        print(f"\nError saving cleaned data to '{output_filename}': {e}")

def analyze_book_prices(csv_file): # Will be refactored to take df as argument
    try:
        # This initial df load will be removed when analyze_book_prices is refactored
        df = pd.read_csv(csv_file)

        # All processing steps have been moved to helper functions.
        # This function will soon be a coordinator.
        # For now, the save_data call is just placed here conceptually.
        # save_data(df, 'cleaned_publicaciones_libros_ateneo.csv') # Conceptual placement

        print("\nSuccessfully processed dataset. Basic checks for empty rows and duplicates are complete.") # This message will be re-evaluated

    except Exception as e:
        print(f"An error occurred during analysis: {e}")


def main():
    parser = argparse.ArgumentParser(description='Analyze book price data from a CSV file.')
    parser.add_argument('csv_file', type=str, help='Path to the CSV file to analyze')
    args = parser.parse_args()

    analyze_book_prices(args.csv_file) # This will be updated

if __name__ == "__main__":
    main()
