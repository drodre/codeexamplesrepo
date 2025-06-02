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
    except Exception as e:
        print(f"An error occurred during data loading: {e}")
        return None

def log_initial_info(df):
    print("First 5 rows of the dataset:")
    print(df.head())
    print("\nColumn names:")
    print(df.columns)
    print(f"Dataset shape: {df.shape}")

def check_data_quality(df):
    print("\n--- Running Data Quality Checks ---")
    # Identify empty rows (all values are NaN)
    empty_rows = df.isnull().all(axis=1)
    num_empty_rows = empty_rows.sum()
    print(f"Number of empty rows (all values NaN): {num_empty_rows}")
    if num_empty_rows > 0:
        print("Indices of empty rows:")
        print(df[empty_rows].index.tolist())

    # Identify duplicate rows based on 'codigo_isbn'
    if 'codigo_isbn' in df.columns:
        duplicates_isbn = df[df.duplicated(subset=['codigo_isbn'], keep=False)]
        num_duplicate_isbn_entries = df.duplicated(subset=['codigo_isbn'], keep='first').sum()
        print(f"Number of duplicate entries based on 'codigo_isbn' (excluding first occurrences): {num_duplicate_isbn_entries}")
        if num_duplicate_isbn_entries > 0:
            print("Duplicate rows (based on 'codigo_isbn', showing all occurrences of duplicates):")
            print(duplicates_isbn.sort_values(by='codigo_isbn'))
    else:
        print("Column 'codigo_isbn' not found, skipping duplicate check based on it.")
    print("--- Data Quality Checks Complete ---")

def process_dates(df):
    print("\n--- Processing 'fecha_publicacion' (Date Column) ---")
    if 'fecha_publicacion' in df.columns:
        df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
        num_nat = df['fecha_publicacion'].isnull().sum()
        print(f"Number of rows with unparseable dates (NaT) in 'fecha_publicacion': {num_nat}")
        print(f"Data type of 'fecha_publicacion' after conversion: {df['fecha_publicacion'].dtype}")
        if len(df) - num_nat > 0:
            print("First 5 values of 'fecha_publicacion' after conversion:")
            print(df['fecha_publicacion'].head())
        else:
            print("No valid dates found in 'fecha_publicacion' after conversion.")
    else:
        print("Column 'fecha_publicacion' not found.")
    print("--- Date Processing Complete ---")
    return df

def process_numeric_columns(df, args):
    print("\n--- Processing Numeric Columns ---")
    # --- Validating and Imputing 'nro_paginas' ---
    if 'nro_paginas' in df.columns:
        print("Processing 'nro_paginas':")
        original_nans_nro_paginas = df['nro_paginas'].isnull().sum()
        df['nro_paginas'] = pd.to_numeric(df['nro_paginas'], errors='coerce')
        coerced_nans_nro_paginas = df['nro_paginas'].isnull().sum() - original_nans_nro_paginas
        print(f"  Number of rows with non-numeric 'nro_paginas' (coerced to NaN): {coerced_nans_nro_paginas}")
        print(f"  Total NaN values in 'nro_paginas' after coercion: {df['nro_paginas'].isnull().sum()}")
        print(f"  Data type of 'nro_paginas' after coercion: {df['nro_paginas'].dtype}")
        print("  Descriptive statistics for 'nro_paginas' before imputation:")
        print(df['nro_paginas'].describe())

        if args.run_data_imputation or args.run_all_processing: # Specific check for imputation part
            nan_count_before_imputation = df['nro_paginas'].isnull().sum()
            if nan_count_before_imputation > 0:
                df['nro_paginas'].fillna(0, inplace=True)
                print(f"  Imputed {nan_count_before_imputation} NaN values in 'nro_paginas' with 0.")
                print("  Descriptive statistics for 'nro_paginas' after imputation:")
                print(df['nro_paginas'].describe())
            else:
                print("  No NaN values to impute in 'nro_paginas'.")

        print("  Potential outliers in 'nro_paginas' (e.g., 1 page or 0 page books post-imputation):")
        one_page_books = df[df['nro_paginas'] == 1]
        zero_page_books = df[df['nro_paginas'] == 0]
        print(f"  Number of books with 1 page: {len(one_page_books)}")
        if not one_page_books.empty: print(one_page_books.head())
        print(f"  Number of books with 0 pages (often due to imputation): {len(zero_page_books)}")
        if not zero_page_books.empty and len(zero_page_books) < 10: print(zero_page_books.head())


    else:
        print("Column 'nro_paginas' not found.")

    # --- Validating 'precio' ---
    if 'precio' in df.columns:
        print("\nProcessing 'precio':")
        original_nans_precio = df['precio'].isnull().sum()
        df['precio'] = pd.to_numeric(df['precio'], errors='coerce')
        coerced_nans_precio = df['precio'].isnull().sum() - original_nans_precio
        print(f"  Number of rows with non-numeric 'precio' (coerced to NaN): {coerced_nans_precio}")
        print(f"  Total NaN values in 'precio' after coercion: {df['precio'].isnull().sum()}")
        print(f"  Data type of 'precio' after coercion: {df['precio'].dtype}")
        print("  Descriptive statistics for 'precio':")
        print(df['precio'].describe())

        print("  Potential outliers in 'precio' (max price books):")
        max_price_val = df['precio'].max()
        if pd.notna(max_price_val):
            max_price_books = df[df['precio'] == max_price_val]
            if not max_price_books.empty:
                print(max_price_books)
            else:
                print("  No books found at the maximum price (this is unexpected if max price was calculated).")
        else:
            print("  Cannot determine maximum price as 'precio' column might be all NaN or empty.")
    else:
        print("Column 'precio' not found.")

    # --- Currency Conversion for 'precio' (ARS to EUR) ---
    if (args.run_price_conversion or args.run_all_processing) and 'precio' in df.columns:
        print("\n--- Currency Conversion 'precio' ARS to EUR ---")
        ars_to_eur_rate = 1340  # 1 EUR = 1340 ARS
        df['precio_eur'] = (df['precio'] / ars_to_eur_rate).round(2)
        print(f"Converted 'precio' to 'precio_eur' using rate: 1 EUR = {ars_to_eur_rate} ARS.")
        print("First 5 rows with ARS and EUR prices:")
        columns_for_price_display = ['precio', 'precio_eur']
        if 'titulo' in df.columns:
            columns_for_price_display.insert(0, 'titulo')
        print(df[columns_for_price_display].head())

        print("\nDescriptive statistics for 'precio_eur':")
        print(df['precio_eur'].describe())
    elif 'precio' not in df.columns and (args.run_price_conversion or args.run_all_processing) :
         print("Column 'precio' not found, skipping currency conversion.")
    print("--- Numeric Column Processing Complete ---")
    return df

def perform_text_cleaning(df):
    print("\n--- Performing Text Column Cleaning ---")
    text_columns_to_clean = [
        'titulo', 'autor', 'editorial', 'idioma',
        'encuadernacion', 'categoria', 'genero', 'subgenero'
    ]
    actual_text_columns_to_clean = [col for col in text_columns_to_clean if col in df.columns]
    print(f"Identified text columns for cleaning: {actual_text_columns_to_clean}")

    for col in actual_text_columns_to_clean:
        df[col] = df[col].astype(str).fillna('')
        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == 'object':
            df[col] = df[col].str.strip()
            df[col] = df[col].str.lower()
            # print(f"Applied basic cleaning (strip, lower) to column: '{col}'") # Verbose
    print("Basic cleaning (strip, lower, astype str) applied to identified text columns.")

    # Specific value replacements
    print("\nApplying Specific Value Replacements...")
    if 'categoria' in df.columns:
        df['categoria'] = df['categoria'].replace('negocios y cs. economicas', 'negocios y ciencias economicas')
        print("  Standardized 'negocios y cs. economicas' to 'negocios y ciencias economicas' in 'categoria'.")
    if 'genero' in df.columns:
        df['genero'] = df['genero'].replace('dep. extremos', 'deportes extremos')
        print("  Standardized 'dep. extremos' to 'deportes extremos' in 'genero'.")
    print("Specific Value Replacements Complete.")

    print("\nInspecting Unique Values in Key Categorical Columns After Cleaning...")
    key_categorical_columns = ['idioma', 'encuadernacion', 'categoria', 'genero']
    for col in key_categorical_columns:
        if col in df.columns:
            unique_values = df[col].unique()
            print(f"  Unique values in '{col}' (sample of up to 10):")
            if len(unique_values) > 10:
                print(f"    {np.random.choice(unique_values, size=10, replace=False)}")
            else:
                print(f"    {unique_values}")
            print(f"  Total unique values in '{col}': {df[col].nunique()}")
        else:
            print(f"  Column '{col}' not found for unique value inspection.")
    print("--- Text Column Cleaning and Inspection Complete ---")
    return df

def generate_and_save_plots(df):
    print("\n--- Generating and Saving EDA Plots ---")

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
                print("No data with 'nro_paginas' > 0 to plot (after imputation).")
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
                print("No data for 'idioma' counts to plot.")
        else:
            print("'idioma' column not found or contains all NaN/empty values. Skipping language counts plot.")
    except Exception as e:
        print(f"Error generating or saving language counts plot: {e}")

    # Plot 4: Scatter plot of nro_paginas (pages > 0) vs precio_eur
    try:
        if 'nro_paginas' in df.columns and 'precio_eur' in df.columns:
            plt.figure(figsize=(10, 6))
            df_filtered_scatter = df[(df['nro_paginas'] > 0) & (df['precio_eur'] > 0)] # Filter 0 pages and 0 price
            if not df_filtered_scatter.empty:
                df_filtered_scatter.plot(kind='scatter', x='nro_paginas', y='precio_eur', alpha=0.5)
                plt.title('Book Price (EUR) vs. Number of Pages (Pages > 0, Price > 0)')
                plt.xlabel('Number of Pages')
                plt.ylabel('Price (EUR)')
                # Log scale for potentially better visualization if price/pages have large range
                # plt.xscale('log')
                # plt.yscale('log')
                plt.grid(True, alpha=0.5)
                plot_filename_scatter = 'price_vs_pages.png'
                plt.savefig(plot_filename_scatter)
                plt.close()
                print(f"Saved price vs. pages scatter plot to '{plot_filename_scatter}'")
            else:
                print("No data with 'nro_paginas' > 0 and 'precio_eur' > 0 to create scatter plot.")
        else:
            print("Columns 'nro_paginas' or 'precio_eur' not found, skipping scatter plot.")
    except Exception as e:
        print(f"Error generating or saving price vs. pages scatter plot: {e}")
    print("--- EDA Plot Generation Complete ---")

def save_data(df, output_filename):
    print(f"\n--- Saving Processed DataFrame to '{output_filename}' ---")
    try:
        df.to_csv(output_filename, index=False)
        print(f"Successfully saved cleaned data to '{output_filename}'")
    except Exception as e:
        print(f"Error saving cleaned data to '{output_filename}': {e}")
    print("--- Data Saving Complete ---")

def analyze_book_prices(df, args):
    try:
        log_initial_info(df)

        output_filename = 'cleaned_dataset.csv' # Default output filename

        if args.run_all_processing:
            print("\n--- Running ALL Processing Steps ---")
            check_data_quality(df)
            df = process_dates(df)
            # process_numeric_columns needs args for its internal imputation/conversion flags
            df = process_numeric_columns(df, args)
            df = perform_text_cleaning(df)
            print("\n--- ALL Processing Steps Complete ---")
        else:
            if args.run_quality_checks:
                check_data_quality(df)
            if args.run_type_conversions: # This implies date conversion and initial numeric conversion
                df = process_dates(df)
                # Call process_numeric_columns but rely on its internal logic for what to do if specific sub-flags aren't set
                # This means basic numeric conversion (to_numeric) will happen.
                # Imputation and price conversion parts within process_numeric_columns are gated by their own specific flags or run_all_processing.
                df = process_numeric_columns(df, args)
            elif args.run_data_imputation or args.run_price_conversion: # If only imputation or price conversion is asked
                 df = process_numeric_columns(df, args)

            if args.run_text_cleaning:
                df = perform_text_cleaning(df)

        if args.save_processed_data:
            save_data(df, output_filename)

        if args.run_eda_plots:
            generate_and_save_plots(df)

        print("\nBook price analysis script execution finished.")

    except Exception as e:
        print(f"An critical error occurred during analysis: {e}")
        # Optionally re-raise if you want the script to exit with an error code
        # raise

def main():
    parser = argparse.ArgumentParser(description='Clean, process, and analyze book price data from a CSV file.')
    parser.add_argument('csv_file', type=str, help='Path to the CSV file to analyze')

    parser.add_argument('--run_quality_checks', action='store_true', help="Run data quality checks (empty rows, duplicates).")
    parser.add_argument('--run_type_conversions', action='store_true', help="Run data type conversions (dates, initial numeric processing).")
    parser.add_argument('--run_data_imputation', action='store_true', help="Run data imputation for 'nro_paginas' (NaN to 0).")
    parser.add_argument('--run_price_conversion', action='store_true', help="Run price conversion from ARS to EUR for 'precio'.")
    parser.add_argument('--run_text_cleaning', action='store_true', help="Run text cleaning operations.")
    parser.add_argument('--run_eda_plots', action='store_true', help="Generate and save EDA plots.")
    parser.add_argument('--save_processed_data', action='store_true', help="Save the processed DataFrame to CSV.")

    parser.add_argument('--run_all_processing', action='store_true',
                        help="Run all core data processing steps: quality checks, type conversions (dates & numeric), 'nro_paginas' imputation, 'precio' to EUR conversion, and text cleaning. This does NOT automatically save data or generate plots unless those specific flags are also set.")

    args = parser.parse_args()

    df = load_data(args.csv_file)

    if df is not None:
        analyze_book_prices(df, args)
    else:
        print("Exiting script due to data loading failure.")

if __name__ == "__main__":
    main()
