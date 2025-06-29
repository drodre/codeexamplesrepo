# Archivo principal para la aplicación web FastAPI del Gestor de Medicamentos.

import os
import sys
from fastapi import FastAPI, Request, Depends, Form, HTTPException # Form, HTTPException añadidos
from fastapi.responses import RedirectResponse # Añadido RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import ValidationError # Para manejar errores de validación de Pydantic
from typing import Optional # Ya estaba, solo para confirmar

# Añadir el directorio de la aplicación al sys.path
# para asegurar que los módulos de 'app' se puedan importar correctamente
# cuando uvicorn ejecuta este archivo desde el directorio raíz del proyecto.
sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Añade 'gestion_medicamentos'
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')) # Si fuera necesario añadir 'app' directamente

try:
    from app import crud, models, database, schemas # Añadir schemas
except ImportError as e:
    print(f"Error importando módulos de app: {e}")
    print(f"sys.path actual: {sys.path}")
    # Esto es un intento de diagnóstico, podría eliminarse después
    # if 'gestion_medicamentos.app' not in sys.modules:
    #     print("Intentando importar app.crud directamente para diagnóstico...")
    #     import app.crud # noqa: F401
    #     print("app.crud importado.")
    #     print("Intentando importar app.schemas directamente para diagnóstico...")
    #     import app.schemas # noqa: F401
    #     print("app.schemas importado.")
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
    # if not medicamentos: # El log ya no es necesario aquí
    #     print("[DEBUG] La lista de medicamentos está vacía.")

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

# --- CRUD Medicamentos ---
# Es importante definir rutas específicas ANTES que rutas con parámetros de path que podrían coincidir.
# Por ejemplo, /medicamentos/nuevo/ DEBE ir ANTES de /medicamentos/{medicamento_id}/

@app.get("/medicamentos/nuevo/", name="crear_medicamento_form")
async def crear_medicamento_form(request: Request):
    return templates.TemplateResponse("form_medicamento.html", {
        "request": request,
        "form_title": "Añadir Nuevo Medicamento",
        "form_action": request.url_for("crear_medicamento_submit"),
        "medicamento": None, # No hay medicamento existente para el formulario de creación
        "errors": None
    })

@app.post("/medicamentos/nuevo/", name="crear_medicamento_submit")
async def crear_medicamento_submit(
    request: Request,
    nombre: str = Form(...),
    marca: Optional[str] = Form(None),
    unidades_por_caja: int = Form(...),
    precio_por_caja_referencia: Optional[float] = Form(None),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    try:
        medicamento_data = schemas.MedicamentoCreate(
            nombre=nombre,
            marca=marca,
            unidades_por_caja=unidades_por_caja,
            precio_por_caja_referencia=precio_por_caja_referencia
        )
    except ValidationError as e:
        errors = e.errors()
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": {"nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja, "precio_por_caja_referencia": precio_por_caja_referencia},
            "errors": errors
        }, status_code=422)

    db_medicamento_existente = crud.obtener_medicamento_por_nombre(db, nombre=medicamento_data.nombre)
    if db_medicamento_existente:
        errors.append({"loc": ["nombre"], "msg": "Ya existe un medicamento con este nombre."})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": medicamento_data.dict(),
            "errors": errors
        }, status_code=400)

    try:
        crud.crear_medicamento(db=db, nombre=medicamento_data.nombre, marca=medicamento_data.marca,
                                             unidades_por_caja=medicamento_data.unidades_por_caja,
                                             precio_referencia=medicamento_data.precio_por_caja_referencia)
        return RedirectResponse(url=request.url_for("listar_todos_medicamentos"), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al guardar el medicamento: {e}"})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": medicamento_data.dict(),
            "errors": errors
        }, status_code=500)

@app.get("/medicamentos/{medicamento_id}/editar/", name="editar_medicamento_form")
async def editar_medicamento_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado")

    return templates.TemplateResponse("form_medicamento.html", {
        "request": request,
        "form_title": f"Editar Medicamento: {medicamento.nombre}",
        "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
        "medicamento": medicamento,
        "errors": None
    })

@app.post("/medicamentos/{medicamento_id}/editar/", name="editar_medicamento_submit")
async def editar_medicamento_submit(
    request: Request,
    medicamento_id: int,
    nombre: str = Form(...),
    marca: Optional[str] = Form(None),
    unidades_por_caja: int = Form(...),
    precio_por_caja_referencia: Optional[float] = Form(None),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    medicamento_original = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento_original:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado para actualizar")

    try:
        medicamento_data_update = schemas.MedicamentoUpdate(
            nombre=nombre,
            marca=marca,
            unidades_por_caja=unidades_por_caja,
            precio_por_caja_referencia=precio_por_caja_referencia
        )
    except ValidationError as e:
        errors = e.errors()
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": {"id": medicamento_id, "nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja, "precio_por_caja_referencia": precio_por_caja_referencia},
            "errors": errors
        }, status_code=422)

    if medicamento_data_update.nombre and medicamento_data_update.nombre.lower() != medicamento_original.nombre.lower():
        db_medicamento_existente = crud.obtener_medicamento_por_nombre(db, nombre=medicamento_data_update.nombre)
        if db_medicamento_existente and db_medicamento_existente.id != medicamento_id:
            errors.append({"loc": ["nombre"], "msg": "Ya existe otro medicamento con este nombre."})
            return templates.TemplateResponse("form_medicamento.html", {
                "request": request,
                "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
                "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
                "medicamento": {"id": medicamento_id, **medicamento_data_update.dict(exclude_unset=True)},
                "errors": errors
            }, status_code=400)

    try:
        update_data_dict = medicamento_data_update.dict(exclude_unset=True)
        if marca == "":
            update_data_dict['marca'] = None
        if precio_por_caja_referencia is None and 'precio_por_caja_referencia' in update_data_dict :
             pass
        elif 'precio_por_caja_referencia' not in update_data_dict and precio_por_caja_referencia is None and medicamento_original.precio_por_caja_referencia is not None:
            update_data_dict['precio_por_caja_referencia'] = None

        if not update_data_dict:
             return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)

        crud.actualizar_medicamento(db, medicamento_id=medicamento_id, datos_actualizacion=update_data_dict)
        return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al actualizar el medicamento: {e}"})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": {"id": medicamento_id, **medicamento_data_update.dict(exclude_unset=True)},
            "errors": errors
        }, status_code=500)

@app.get("/medicamentos/{medicamento_id}/eliminar/", name="eliminar_medicamento_confirm_form")
async def eliminar_medicamento_confirm_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado")

    return templates.TemplateResponse("confirmar_eliminacion_medicamento.html", {
        "request": request,
        "medicamento": medicamento,
        "title": f"Confirmar Eliminación: {medicamento.nombre}"
    })

@app.post("/medicamentos/{medicamento_id}/eliminar/", name="eliminar_medicamento_submit")
async def eliminar_medicamento_submit(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado para eliminar")

    try:
        crud.eliminar_medicamento(db, medicamento_id=medicamento_id)
        return RedirectResponse(url=request.url_for("listar_todos_medicamentos"), status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el medicamento: {e}")

# Esta es la ruta que causaba el problema, la movemos después de las de CRUD
@app.get("/medicamentos/{medicamento_id}/", name="detalle_medicamento")
async def detalle_medicamento(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        return templates.TemplateResponse("error_404.html", {"request": request, "detail": f"Medicamento con ID {medicamento_id} no encontrado"}, status_code=404)

    lotes = crud.obtener_lotes_por_medicamento(db, medicamento_id=medicamento_id, solo_activos=False)
    stock_total = crud.calcular_stock_total_unidades(db, medicamento_id=medicamento_id)
    vencimiento_proximo = crud.calcular_fecha_vencimiento_proxima(db, medicamento_id=medicamento_id)

    from datetime import date as py_date

    return templates.TemplateResponse("detalle_medicamento.html", {
        "request": request,
        "medicamento": medicamento,
        "lotes": lotes,
        "stock_total": stock_total,
        "vencimiento_proximo": vencimiento_proximo,
        "today_date": py_date.today(),
        "title": f"Detalle: {medicamento.nombre}"
    })

@app.get("/pedidos/", name="listar_todos_pedidos")
async def listar_todos_pedidos(request: Request, db: Session = Depends(get_db_session_fastapi)):
    pedidos = crud.obtener_pedidos(db, limit=1000)

    pedidos_info = []
    for p in pedidos:
        costo_total = crud.calcular_costo_total_pedido(db, p.id)
        pedidos_info.append({
            "pedido": p,
            "costo_total": costo_total
        })

    return templates.TemplateResponse("lista_pedidos.html", {
        "request": request,
        "pedidos_info": pedidos_info,
        "title": "Lista de Pedidos"
    })

@app.get("/pedidos/{pedido_id}/", name="detalle_pedido")
async def detalle_pedido_ruta(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        return templates.TemplateResponse("error_404.html", {"request": request, "detail": f"Pedido con ID {pedido_id} no encontrado"}, status_code=404)

    detalles_pedido = crud.obtener_detalles_por_pedido(db, pedido_id=pedido_id)
    costo_total = crud.calcular_costo_total_pedido(db, pedido_id=pedido_id) # Ya se calcula en la plantilla, pero útil tenerlo aquí

    # Para mostrar el nombre del medicamento en los detalles del pedido,
    # nos aseguramos de que el objeto medicamento esté accesible.
    # crud.obtener_detalles_por_pedido ya debería cargar la relación si está configurada con eager loading,
    # o se accederá por lazy loading en la plantilla. Si no, tendríamos que cargarlo explícitamente.
    # La plantilla actual accede a detalle.medicamento.nombre, lo que implica que la relación funciona.

    return templates.TemplateResponse("detalle_pedido.html", {
        "request": request,
        "pedido": pedido,
        "detalles_pedido": detalles_pedido,
        "costo_total": costo_total,
        "title": f"Detalle Pedido #{pedido.id}"
    })

# --- CRUD Medicamentos ---
from fastapi import Form, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import ValidationError # Para manejar errores de validación de Pydantic

@app.get("/medicamentos/nuevo/", name="crear_medicamento_form")
async def crear_medicamento_form(request: Request):
    return templates.TemplateResponse("form_medicamento.html", {
        "request": request,
        "form_title": "Añadir Nuevo Medicamento",
        "form_action": request.url_for("crear_medicamento_submit"),
        "medicamento": None, # No hay medicamento existente para el formulario de creación
        "errors": None
    })

@app.post("/medicamentos/nuevo/", name="crear_medicamento_submit")
async def crear_medicamento_submit(
    request: Request,
    nombre: str = Form(...),
    marca: Optional[str] = Form(None),
    unidades_por_caja: int = Form(...),
    precio_por_caja_referencia: Optional[float] = Form(None),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    try:
        # Validar con Pydantic Schema
        medicamento_data = schemas.MedicamentoCreate(
            nombre=nombre,
            marca=marca,
            unidades_por_caja=unidades_por_caja,
            precio_por_caja_referencia=precio_por_caja_referencia
        )
    except ValidationError as e:
        errors = e.errors()
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": {"nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja, "precio_por_caja_referencia": precio_por_caja_referencia}, # Re-popular con datos ingresados
            "errors": errors
        }, status_code=422) # Unprocessable Entity

    # Verificar si ya existe un medicamento con el mismo nombre
    db_medicamento_existente = crud.obtener_medicamento_por_nombre(db, nombre=medicamento_data.nombre)
    if db_medicamento_existente:
        errors.append({"loc": ["nombre"], "msg": "Ya existe un medicamento con este nombre."})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": medicamento_data.dict(), # Re-popular con datos ingresados
            "errors": errors
        }, status_code=400) # Bad Request

    try:
        medicamento = crud.crear_medicamento(db=db, nombre=medicamento_data.nombre, marca=medicamento_data.marca,
                                             unidades_por_caja=medicamento_data.unidades_por_caja,
                                             precio_referencia=medicamento_data.precio_por_caja_referencia)
        # Redirigir a la lista de medicamentos o al detalle del nuevo medicamento
        # Por ahora, a la lista.
        return RedirectResponse(url=request.url_for("listar_todos_medicamentos"), status_code=303) # See Other
    except Exception as e:
        # Manejo de otros errores inesperados de la base de datos
        # Idealmente, loggear el error `e`
        errors.append({"loc": ["general"], "msg": f"Error inesperado al guardar el medicamento: {e}"})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": medicamento_data.dict(),
            "errors": errors
        }, status_code=500) # Internal Server Error

@app.get("/medicamentos/{medicamento_id}/editar/", name="editar_medicamento_form")
async def editar_medicamento_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        # Podríamos usar la plantilla error_404.html o lanzar HTTPException
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado")

    return templates.TemplateResponse("form_medicamento.html", {
        "request": request,
        "form_title": f"Editar Medicamento: {medicamento.nombre}",
        "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
        "medicamento": medicamento, # Pasar el medicamento existente para pre-rellenar el formulario
        "errors": None
    })

@app.post("/medicamentos/{medicamento_id}/editar/", name="editar_medicamento_submit")
async def editar_medicamento_submit(
    request: Request,
    medicamento_id: int,
    nombre: str = Form(...),
    marca: Optional[str] = Form(None),
    unidades_por_caja: int = Form(...),
    precio_por_caja_referencia: Optional[float] = Form(None),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    # Obtener el medicamento original para comparar y para re-popular en caso de error
    medicamento_original = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento_original:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado para actualizar")

    try:
        # Usar MedicamentoUpdate implica que todos los campos son opcionales,
        # pero aquí los estamos recibiendo todos del formulario.
        # Si quisiéramos una actualización parcial real (PATCH), el enfoque sería diferente.
        # Por ahora, tratamos esto como un PUT donde todos los valores se re-envían.
        medicamento_data_update = schemas.MedicamentoUpdate(
            nombre=nombre,
            marca=marca,
            unidades_por_caja=unidades_por_caja,
            precio_por_caja_referencia=precio_por_caja_referencia
        )
    except ValidationError as e:
        errors = e.errors()
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": {"id": medicamento_id, "nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja, "precio_por_caja_referencia": precio_por_caja_referencia},
            "errors": errors
        }, status_code=422)

    # Verificar si el nuevo nombre ya existe en OTRO medicamento
    if medicamento_data_update.nombre and medicamento_data_update.nombre.lower() != medicamento_original.nombre.lower():
        db_medicamento_existente = crud.obtener_medicamento_por_nombre(db, nombre=medicamento_data_update.nombre)
        if db_medicamento_existente and db_medicamento_existente.id != medicamento_id:
            errors.append({"loc": ["nombre"], "msg": "Ya existe otro medicamento con este nombre."})
            return templates.TemplateResponse("form_medicamento.html", {
                "request": request,
                "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
                "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
                "medicamento": {"id": medicamento_id, **medicamento_data_update.dict(exclude_unset=True)}, # Re-popular con datos ingresados
                "errors": errors
            }, status_code=400)

    try:
        # Construir el diccionario de datos para actualizar, solo con los campos que tienen valor.
        # crud.actualizar_medicamento espera un dict.
        update_data_dict = medicamento_data_update.dict(exclude_unset=True)

        # Si un campo opcional se deja vacío en el formulario y era None, exclude_unset=True lo quitará.
        # Si queremos que un campo vacío en el form signifique "poner a None", necesitamos manejarlo.
        # Por ejemplo, si 'marca' se envía como string vacío y queremos que sea None en BD:
        if marca == "":
            update_data_dict['marca'] = None
        if precio_por_caja_referencia is None and 'precio_por_caja_referencia' in update_data_dict :
             # Si el Form lo interpreta como None (ej. campo vacío no numérico), y queremos asegurar que se actualice a None
             pass # ya estaría como None si el modelo Pydantic lo permite.
        elif 'precio_por_caja_referencia' not in update_data_dict and precio_por_caja_referencia is None and medicamento_original.precio_por_caja_referencia is not None:
            # Si el campo no se envió (o fue None) y antes tenía valor, explícitamente ponerlo a None
            update_data_dict['precio_por_caja_referencia'] = None


        if not update_data_dict: # Si no hay nada que actualizar (todos los campos son iguales o no se enviaron)
             return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)

        medicamento = crud.actualizar_medicamento(db, medicamento_id=medicamento_id, datos_actualizacion=update_data_dict)
        if not medicamento:
             # Esto no debería ocurrir si la verificación de existencia al inicio fue correcta
            raise HTTPException(status_code=404, detail="Medicamento no encontrado después de intentar actualizar.")

        return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al actualizar el medicamento: {e}"})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request,
            "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": {"id": medicamento_id, **medicamento_data_update.dict(exclude_unset=True)},
            "errors": errors
        }, status_code=500)

@app.get("/medicamentos/{medicamento_id}/eliminar/", name="eliminar_medicamento_confirm_form")
async def eliminar_medicamento_confirm_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado")

    return templates.TemplateResponse("confirmar_eliminacion_medicamento.html", {
        "request": request,
        "medicamento": medicamento,
        "title": f"Confirmar Eliminación: {medicamento.nombre}"
    })

@app.post("/medicamentos/{medicamento_id}/eliminar/", name="eliminar_medicamento_submit")
async def eliminar_medicamento_submit(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        # Aunque el GET previo debería haberlo capturado, es buena práctica verificar de nuevo.
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado para eliminar")

    try:
        eliminado = crud.eliminar_medicamento(db, medicamento_id=medicamento_id)
        if not eliminado:
            # Esto podría ocurrir si hay un problema de concurrencia o un error en la lógica de crud.eliminar_medicamento
            # que no lanza una excepción pero falla.
            # Por ahora, asumimos que si no lanza excepción y devuelve False (aunque nuestro crud.eliminar_medicamento devuelve True/False)
            # o si el objeto ya no está (aunque ya lo verificamos), es un error.
            # Sin embargo, crud.eliminar_medicamento ya maneja la no existencia.
             raise HTTPException(status_code=500, detail=f"No se pudo eliminar el medicamento ID {medicamento_id} por una razón desconocida.")

        # Aquí podríamos añadir un mensaje flash para mostrar en la página de lista.
        # FastAPI no tiene soporte nativo para mensajes flash como Flask/Django.
        # Se necesitaría una solución personalizada (ej. cookies, o pasar un parámetro en la URL).
        # Por ahora, solo redirigimos.
        return RedirectResponse(url=request.url_for("listar_todos_medicamentos"), status_code=303)
    except Exception as e:
        # Idealmente, loggear el error 'e'
        # Y mostrar un error más amigable o redirigir a una página de error.
        raise HTTPException(status_code=500, detail=f"Error al eliminar el medicamento: {e}")


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
