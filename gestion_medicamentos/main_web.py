# Archivo principal para la aplicación web FastAPI del Gestor de Medicamentos.

import os
import sys
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Añadir el directorio de la aplicación al sys.path
# para asegurar que los módulos de 'app' se puedan importar correctamente
# cuando uvicorn ejecuta este archivo desde el directorio raíz del proyecto.
sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Añade 'gestion_medicamentos'
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')) # Si fuera necesario añadir 'app' directamente

try:
    from app import crud, models, database
except ImportError as e:
    print(f"Error importando módulos de app: {e}")
    print(f"sys.path actual: {sys.path}")
    # Esto es un intento de diagnóstico, podría eliminarse después
    # if 'gestion_medicamentos.app' not in sys.modules:
    #     print("Intentando importar app.crud directamente para diagnóstico...")
    #     import app.crud
    #     print("app.crud importado.")
    raise

app = FastAPI(title="Gestor de Medicamentos Caseros - Web", version="0.1.0")

# Configuración de plantillas Jinja2
# La ruta a las plantillas es relativa al directorio donde se ejecuta uvicorn,
# o podemos hacerla absoluta.
# Si uvicorn se ejecuta desde la raíz del repo: "gestion_medicamentos/web/templates"
# Si uvicorn se ejecuta desde gestion_medicamentos/: "web/templates"
# Para mayor robustez, construimos una ruta absoluta:
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "web", "templates")
templates = Jinja2Templates(directory=templates_dir)


# Dependencia para obtener la sesión de base de datos para FastAPI
def get_db_session_fastapi():
    db = None
    try:
        db = database.SessionLocal()
        yield db
    finally:
        if db:
            db.close()

@app.get("/", name="root") # Añadido name="root" para url_for si se usa en plantillas
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Página de Inicio"})

@app.get("/medicamentos/", name="listar_todos_medicamentos")
async def listar_todos_medicamentos(request: Request, db: Session = Depends(get_db_session_fastapi)):
    medicamentos = crud.obtener_medicamentos(db, limit=1000) # Obtener todos los medicamentos

    medicamentos_info = []
    for med in medicamentos:
        stock_total = crud.calcular_stock_total_unidades(db, med.id)
        vencimiento_proximo = crud.calcular_fecha_vencimiento_proxima(db, med.id)
        medicamentos_info.append({
            "medicamento": med,
            "stock_total": stock_total,
            "vencimiento_proximo": vencimiento_proximo
        })

    return templates.TemplateResponse("lista_medicamentos.html", {
        "request": request,
        "medicamentos_info": medicamentos_info,
        "title": "Lista de Medicamentos"
    })

@app.get("/medicamentos/{medicamento_id}/", name="detalle_medicamento")
async def detalle_medicamento(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        # Idealmente, aquí se mostraría una página de error 404.
        # Por ahora, una simple respuesta o redirigir.
        # O podríamos pasar None a la plantilla y que ella maneje el "no encontrado".
        return templates.TemplateResponse("error_404.html", {"request": request, "detail": f"Medicamento con ID {medicamento_id} no encontrado"}, status_code=404)

    lotes = crud.obtener_lotes_por_medicamento(db, medicamento_id=medicamento_id, solo_activos=False) # Mostrar todos los lotes
    stock_total = crud.calcular_stock_total_unidades(db, medicamento_id=medicamento_id)
    vencimiento_proximo = crud.calcular_fecha_vencimiento_proxima(db, medicamento_id=medicamento_id)

    # Para la columna "Activo" en la tabla de lotes, necesitamos la fecha de hoy en la plantilla.
    from datetime import date as py_date # Renombrar para evitar conflicto con models.Date

    return templates.TemplateResponse("detalle_medicamento.html", {
        "request": request,
        "medicamento": medicamento,
        "lotes": lotes,
        "stock_total": stock_total,
        "vencimiento_proximo": vencimiento_proximo,
        "today_date": py_date.today(), # Pasar la fecha de hoy a la plantilla
        "title": f"Detalle: {medicamento.nombre}"
    })

# Aquí se añadirán más rutas.

if __name__ == "__main__":
    # Esto es solo para referencia, la ejecución se hará con uvicorn.
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    print("Para ejecutar esta aplicación web, use el comando:")
    print("uvicorn gestion_medicamentos.main_web:app --reload --port 8000")
    print(f"Asegúrese de estar en el directorio raíz del repositorio ('{os.path.dirname(current_dir)}') al ejecutar uvicorn.")

# Ejemplo de cómo se usaría la sesión en una ruta:
# @app.get("/alguna_ruta")
# async def alguna_funcion(request: Request, db: Session = Depends(get_db_session_fastapi)):
#     # usar db para llamar a funciones crud
#     items = crud.obtener_medicamentos(db, limit=10)
#     return templates.TemplateResponse("alguna_plantilla.html", {"request": request, "items": items})
