# Laravel Hello World

This is a minimal Laravel application that responds with "Hello World from Laravel!".

It's intended as a sample application for testing CI/CD pipelines, demonstrating a basic Laravel setup.

## Prerequisites

*   PHP 8.1+
*   Composer
*   Docker (optional, for containerized execution)
*   Node.js & NPM (for frontend asset compilation, though not strictly needed for this minimal example if you don't modify frontend assets)

## Environment Configuration (`.env` file)

Laravel requires an `.env` file for configuration.

1.  **Copy the example file:**
    ```bash
    cp .env.example .env
    ```
2.  **Generate an application key:** This is crucial for securing your application.
    ```bash
    php artisan key:generate
    ```
3.  **Configure other settings (if necessary):** For this simple application, the defaults for `APP_NAME`, `APP_ENV`, `APP_DEBUG`, `APP_URL`, database, cache, and session drivers in the copied `.env` file are generally fine for local testing. For a production-like Docker build, you'd typically set:
    *   `APP_ENV=production`
    *   `APP_DEBUG=false`
    *   Ensure `APP_KEY` is set (either by running `php artisan key:generate` before building or by injecting it during your CI/CD process).

**Important:** The `.env` file should NEVER be committed to version control. The `.gitignore` file is already configured to ignore it.

## Running Locally

1.  **Clone the repository (if you haven't already).**
2.  **Navigate to this directory:**
    ```bash
    cd php/laravel-helloworld
    ```
3.  **Install PHP dependencies:**
    ```bash
    composer install
    ```
4.  **Set up your `.env` file:** Follow the instructions under "Environment Configuration (`.env` file)" above.
5.  **Run the development server:**
    ```bash
    php artisan serve
    ```
    The application will typically be available at `http://localhost:8000`.

## Running with Docker

1.  **Navigate to this directory:**
    ```bash
    cd php/laravel-helloworld
    ```
2.  **Prepare the `.env` file for Docker:**
    *   Copy `.env.example` to `.env`: `cp .env.example .env`
    *   Generate an application key: `php artisan key:generate` (this will write the key to your local `.env` file).
    *   Modify any other necessary variables in the `.env` file (e.g., `APP_ENV=production`, `APP_DEBUG=false`). The Docker build process will copy this `.env` file into the image.
3.  **Build the Docker image:**
    ```bash
    docker build -t laravel-helloworld .
    ```
4.  **Run the Docker container:**
    ```bash
    docker run -p 8080:80 laravel-helloworld
    ```
    The application will be available at `http://localhost:8080` (note the port mapping from container's port 80).
