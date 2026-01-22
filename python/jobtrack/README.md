# Jobtrack Application

Esta aplicación busca en InfoJobs ofertas de trabajo de DevOps.

## Configuración

1.  Crea un entorno virtual:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

3.  Crea un archivo `config.json` a partir del ejemplo:
    ```bash
    cp config.json.example config.json
    ```

4.  Edita `config.json` con tus credenciales de la API de InfoJobs.

## Uso

Ejecuta la aplicación:
```bash
python3 src/main.py
```
