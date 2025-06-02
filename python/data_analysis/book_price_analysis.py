import pandas as pd
import numpy as np
import argparse
import matplotlib.pyplot as plt

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

        # --- Text Column Cleaning ---
        print("\n--- Preparing for Text Column Cleaning ---")
        text_columns_to_clean = [
            'titulo', 'autor', 'editorial', 'idioma', 
            'encuadernacion', 'categoria', 'genero', 'subgenero'
        ]
        # Ensure all listed columns exist in the DataFrame to avoid errors during cleaning
        text_columns_to_clean = [col for col in text_columns_to_clean if col in df.columns]
        print(f"Identified text columns for cleaning: {text_columns_to_clean}")

        for col in text_columns_to_clean:
            # Ensure column is treated as string, fill NaNs with empty string for string operations
            # NaNs might have been introduced if a column was unexpectedly numeric/boolean and then selected.
            # Or they might be original NaNs. Treating as empty string for .str methods to work.
            df[col] = df[col].astype(str).fillna('') # Convert to string and fill potential NaNs
            # Check if column is not purely numeric before applying string methods more suited for text
            # This is a safeguard, though astype(str) handles most things.
            # We expect these to be text, but good to be cautious.
            if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == 'object':
                df[col] = df[col].str.strip()
                df[col] = df[col].str.lower()
                print(f"Applied basic cleaning (strip, lower) to column: '{col}'")
            else:
                print(f"Skipped string methods for column: '{col}' as it's not predominantly string-like after astype(str). Current dtype: {df[col].dtype}")
        # Replace empty strings that resulted from NaNs or were original empty strings with np.nan 
        # if you want to maintain NaN for truly missing values after cleaning.
        # This step is optional and depends on how you want to treat genuinely empty text fields vs. original NaNs.
        # For now, we'll leave them as empty strings as per .fillna(''). If NaNs are preferred:
        # for col in text_columns_to_clean:
        #     df[col] = df[col].replace('', np.nan)
        # print("Replaced empty strings with np.nan where applicable after cleaning.")

        # Specific value replacements
        print("\n--- Applying Specific Value Replacements ---")

        # For 'categoria'
        if 'categoria' in df.columns:
            df['categoria'] = df['categoria'].replace('negocios y cs. economicas', 'negocios y ciencias economicas')
            print("Standardized 'negocios y cs. economicas' to 'negocios y ciencias economicas' in 'categoria'.")

        # For 'genero'
        if 'genero' in df.columns:
            df['genero'] = df['genero'].replace('dep. extremos', 'deportes extremos')
            print("Standardized 'dep. extremos' to 'deportes extremos' in 'genero'.")

        print("--- Specific Value Replacements Complete ---")

        print("\n--- Inspecting Unique Values in Key Categorical Columns After Basic Cleaning ---")
        key_categorical_columns = ['idioma', 'encuadernacion', 'categoria', 'genero']

        #     df[col] = df[col].replace('', np.nan) 
        # print("Replaced empty strings with np.nan where applicable after cleaning.")

        print("\n--- Inspecting Unique Values in Key Categorical Columns After Basic Cleaning ---")
        key_categorical_columns = ['idioma', 'encuadernacion', 'categoria', 'genero']
        
        for col in key_categorical_columns:
            if col in df.columns: # Check if column exists
                unique_values = df[col].unique()
                print(f"Unique values in '{col}' (sample of up to 20):")
                # Print all if less than 20, otherwise print a sample to keep output manageable
                if len(unique_values) > 20:
                    print(np.random.choice(unique_values, size=20, replace=False)) # Show a random sample
                else:
                    print(unique_values)
                print(f"Total unique values in '{col}': {df[col].nunique()}")
            else:
                print(f"Column '{col}' not found in DataFrame for unique value inspection.")
        print("--- End of Unique Value Inspection ---")

        # --- Save the cleaned DataFrame ---
        output_filename = 'cleaned_publicaciones_libros_ateneo.csv'
        try:
            df.to_csv(output_filename, index=False)
            print(f"\nSuccessfully saved cleaned data to '{output_filename}'")
        except Exception as e:
            print(f"\nError saving cleaned data to '{output_filename}': {e}")

        # --- Generate and Save Plots ---
        print("\n--- Generating and Saving Plots ---")

        # Plot 1: Distribution of precio_eur
        try:
            plt.figure(figsize=(10, 6))
            df['precio_eur'].plot(kind='hist', bins=50, edgecolor='black')
            plt.title('Distribution of Book Prices (EUR)')
            plt.xlabel('Price (EUR)')
            plt.ylabel('Frequency')
            plt.grid(axis='y', alpha=0.75)
            plot_filename_price = 'precio_eur_distribution.png'
            plt.savefig(plot_filename_price)
            plt.close() # Close the figure to free memory
            print(f"Saved price distribution plot to '{plot_filename_price}'")
        except Exception as e:
            print(f"Error generating or saving price distribution plot: {e}")

        # Plot 2: Distribution of nro_paginas (pages > 0)
        try:
            plt.figure(figsize=(10, 6))
            # Filter out rows where nro_paginas is 0 (our imputed value for NaN)
            df_filtered_pages = df[df['nro_paginas'] > 0]
            if not df_filtered_pages.empty:
                df_filtered_pages['nro_paginas'].plot(kind='hist', bins=50, edgecolor='black')
                plt.title('Distribution of Book Page Numbers (Pages > 0)')
                plt.xlabel('Number of Pages')
                plt.ylabel('Frequency')
                plt.grid(axis='y', alpha=0.75)
                plot_filename_pages = 'nro_paginas_distribution.png'
                plt.savefig(plot_filename_pages)
                plt.close() # Close the figure to free memory
                print(f"Saved page number distribution plot to '{plot_filename_pages}'")
            else:
                print("No data with 'nro_paginas' > 0 to plot.")
        except Exception as e:
            print(f"Error generating or saving page number distribution plot: {e}")

        # Plot 3: Book Counts by idioma (Top 10)
        try:
            plt.figure(figsize=(12, 7)) # Adjusted figure size for better label display
            top_n_languages = 10
            # Ensure 'idioma' column exists and is not all NaN, then proceed
            if 'idioma' in df.columns and df['idioma'].notna().any():
                idioma_counts = df['idioma'].value_counts().nlargest(top_n_languages)
                if not idioma_counts.empty:
                    idioma_counts.plot(kind='bar', edgecolor='black')
                    plt.title(f'Top {top_n_languages} Book Languages')
                    plt.xlabel('Idioma (Language)')
                    plt.ylabel('Number of Books')
                    plt.xticks(rotation=45, ha='right') # Rotate labels for better readability
                    plt.tight_layout() # Adjust layout to prevent labels from being cut off
                    plt.grid(axis='y', alpha=0.75)
                    plot_filename_idioma = 'idioma_counts.png'
                    plt.savefig(plot_filename_idioma)
                    plt.close() # Close the figure to free memory
                    print(f"Saved language counts plot to '{plot_filename_idioma}'")
                else:
                    print("No data for 'idioma' counts to plot (perhaps all NaN or empty after filtering).")
            else:
                print("'idioma' column not found or contains all NaN values. Skipping plot.")
        except Exception as e:
            print(f"Error generating or saving language counts plot: {e}")

        # Plot 4: Scatter plot of nro_paginas (pages > 0) vs precio_eur
        try:
            plt.figure(figsize=(10, 6))
            # Filter out rows where nro_paginas is 0 for a more meaningful scatter plot
            df_filtered_scatter = df[df['nro_paginas'] > 0]
            if not df_filtered_scatter.empty:
                # Using a smaller alpha for transparency to see point density
                df_filtered_scatter.plot(kind='scatter', x='nro_paginas', y='precio_eur', alpha=0.5)
                plt.title('Book Price (EUR) vs. Number of Pages (Pages > 0)')
                plt.xlabel('Number of Pages')
                plt.ylabel('Price (EUR)')
                plt.grid(True, alpha=0.5)
                plot_filename_scatter = 'price_vs_pages.png'
                plt.savefig(plot_filename_scatter)
                plt.close() # Close the figure to free memory
                print(f"Saved price vs. pages scatter plot to '{plot_filename_scatter}'")
            else:
                print("No data with 'nro_paginas' > 0 to create scatter plot.")
        except Exception as e:
            print(f"Error generating or saving price vs. pages scatter plot: {e}")

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
