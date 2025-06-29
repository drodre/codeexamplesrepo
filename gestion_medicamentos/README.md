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

## Ejecución de las Aplicaciones

Este proyecto cuenta con dos interfaces: una de Línea de Comandos (CLI) y una Web.

### 1. Ejecución de la Aplicación (CLI)

La CLI permite una gestión más directa y detallada de los datos.

Una vez completada la configuración inicial (ver arriba, incluye instalación de `requirements.txt`), puedes ejecutar la aplicación de línea de comandos. Asegúrate de estar en el directorio `gestion_medicamentos`:

```bash
python main_cli.py
```

Esto iniciará la interfaz de línea de comandos. La base de datos (`medicamentos.db`) se creará automáticamente dentro de la carpeta `data/` la primera vez que ejecutes la aplicación si no existe.

### 2. Ejecución de la Aplicación Web (FastAPI)

La interfaz web proporciona una visualización de los datos.

Asegúrate de haber instalado todas las dependencias, incluyendo `fastapi` y `uvicorn`.

Para ejecutar la aplicación web, navega al **directorio raíz del repositorio** (el que contiene la carpeta `gestion_medicamentos`) y ejecuta el siguiente comando:

```bash
uvicorn gestion_medicamentos.main_web:app --reload --port 8000
```

Explicación del comando:
- `uvicorn`: Es el servidor ASGI que ejecutará la aplicación FastAPI.
- `gestion_medicamentos.main_web:app`: Le dice a uvicorn dónde encontrar la instancia de FastAPI.
  - `gestion_medicamentos.main_web`: Es el módulo Python (el archivo `main_web.py` dentro de la carpeta `gestion_medicamentos`).
  - `app`: Es el nombre de la variable (la instancia de FastAPI) dentro de `main_web.py`.
- `--reload`: Hace que el servidor se reinicie automáticamente cada vez que detecta cambios en el código (muy útil durante el desarrollo).
- `--port 8000`: Especifica el puerto en el que se ejecutará la aplicación. Puedes cambiarlo si es necesario.

Una vez que el servidor esté en marcha, podrás acceder a la aplicación web abriendo tu navegador y visitando: `http://127.0.0.1:8000`
