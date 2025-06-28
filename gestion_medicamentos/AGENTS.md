# Directrices para el Agente de IA

Este archivo contiene directrices para el agente de IA que trabaja en el proyecto de Gestión de Medicamentos.

## Convenciones de Código

- **Lenguaje:** Python 3.9 o superior.
- **Estilo de Código:** Seguir las convenciones de [PEP 8](https://www.python.org/dev/peps/pep-0008/).
- **Documentación:**
    - Todas las funciones y clases deben tener docstrings claros y concisos.
    - Utilizar type hinting para mejorar la legibilidad y mantenibilidad del código.
- **Pruebas:**
    - Escribir pruebas unitarias para todas las funcionalidades nuevas.
    - Las pruebas deben estar ubicadas en la carpeta `tests`.
    - Intentar alcanzar una alta cobertura de código.
- **Manejo de Dependencias:**
    - Utilizar un archivo `requirements.txt` para gestionar las dependencias del proyecto.
- **Commits:**
    - Escribir mensajes de commit claros y descriptivos, siguiendo el [estilo convencional de commits](https://www.conventionalcommits.org/).

## Estructura del Proyecto

- **`app/`**: Contiene el código principal de la aplicación.
    - `app/models.py`: Definición de las estructuras de datos (medicamentos, pedidos, etc.).
    - `app/logic.py` o `app/services.py`: Lógica de negocio de la aplicación.
    - `app/main.py`: Punto de entrada de la aplicación (si es una aplicación de consola o API).
    - `app/ui.py` o `app/views.py`: Código relacionado con la interfaz de usuario (si aplica).
- **`data/`**: Almacenamiento de datos. Inicialmente se pueden usar archivos CSV o JSON.
- **`tests/`**: Pruebas unitarias.

## Flujo de Trabajo

1.  **Comprender los Requisitos:** Asegúrate de entender completamente la tarea o el problema a resolver.
2.  **Planificación:** Antes de escribir código, crea un plan detallado de los pasos a seguir.
3.  **Desarrollo Iterativo:**
    *   Implementa pequeñas piezas de funcionalidad.
    *   Escribe pruebas para cada pieza.
    *   Refactoriza según sea necesario.
4.  **Pruebas:** Ejecuta todas las pruebas para asegurar que no haya regresiones.
5.  **Documentación:** Actualiza la documentación relevante.

## Herramientas y Tecnologías

- **Interfaz de Usuario:** Aunque Python no es el más habitual para frontend, se explorarán opciones como Tkinter, PyQt, o librerías web como Flask/Django si se decide crear una interfaz web más adelante. Inicialmente, se puede comenzar con una interfaz de línea de comandos (CLI).
- **Almacenamiento de Datos:**
    - Para empezar: Archivos CSV o JSON.
    - Posible evolución: SQLite o una base de datos más robusta si la complejidad aumenta.

## Comunicación

- Si encuentras ambigüedades o necesitas aclaraciones, pregunta al usuario.
- Informa al usuario sobre el progreso y cualquier decisión importante tomada.

## Consideraciones Específicas del Proyecto

- **Sensibilidad de los Datos:** Aunque es un proyecto para uso doméstico, ten en cuenta la privacidad si se manejaran datos personales (no es el caso inicialmente con solo nombres de medicamentos y fechas).
- **Usabilidad:** Intenta que la aplicación sea fácil de usar, incluso si es a través de una CLI.

---

*Este archivo `AGENTS.md` puede ser actualizado a medida que el proyecto evoluciona.*
