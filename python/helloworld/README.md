# Python Hello World (Flask)

This is a very simple Python web application built with Flask that responds with "Hello World from Python!".

It's intended as a sample application for testing CI/CD pipelines.

## Prerequisites

*   Python 3.8+
*   pip (Python package installer)
*   Docker (optional, for containerized execution)

## Running Locally

1.  **Clone the repository (if you haven't already).**
2.  **Navigate to this directory:**
    ```bash
    cd python/helloworld
    ```
3.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will be available at `http://localhost:8080`.

## Running with Docker

1.  **Build the Docker image:**
    ```bash
    docker build -t python-helloworld .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 8080:8080 python-helloworld
    ```
    The application will be available at `http://localhost:8080`.
