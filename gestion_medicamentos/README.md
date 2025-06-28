# Gestión de Medicamentos

Este proyecto es una aplicación sencilla para gestionar los medicamentos de uso doméstico.

Permitirá:
- Registrar medicamentos.
- Controlar la cantidad disponible.
- Registrar la fecha de caducidad del stock.
- Almacenar el precio del medicamento.
- Gestionar los pedidos realizados.

La aplicación está siendo desarrollada en Python.

## Requisitos

- Python 3.7+
- SQLAlchemy (y sus dependencias)

## Configuración Inicial

1.  **Clonar el repositorio (si aplica) o descargar los archivos.**
2.  **Navegar a la carpeta `gestion_medicamentos`:**
    ```bash
    cd ruta/al/repositorio/gestion_medicamentos
    ```
3.  **Crear un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    ```
4.  **Activar el entorno virtual:**
    *   En Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   En macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
5.  **Instalar las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
    Esto instalará SQLAlchemy.

## Ejecución de la Aplicación (CLI)

Una vez completada la configuración inicial, puedes ejecutar la aplicación de línea de comandos desde el directorio `gestion_medicamentos`:

```bash
python main_cli.py
```

Esto iniciará la interfaz de línea de comandos donde podrás interactuar con las diferentes funcionalidades de la aplicación. La base de datos (`medicamentos.db`) se creará automáticamente dentro de la carpeta `data/` la primera vez que ejecutes la aplicación si no existe.
