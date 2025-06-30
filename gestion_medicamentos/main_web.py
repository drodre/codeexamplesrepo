# Archivo principal para la aplicación web FastAPI del Gestor de Medicamentos.

import os
import sys
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import ValidationError
from typing import Optional

# Añadir el directorio de la aplicación al sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import crud, models, database, schemas
except ImportError as e:
    print(f"Error importando módulos de app: {e}")
    print(f"sys.path actual: {sys.path}")
    raise

app = FastAPI(title="Gestor de Medicamentos Caseros - Web", version="0.1.0")

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "web", "templates")
templates = Jinja2Templates(directory=templates_dir)

def get_db_session_fastapi():
    db = None
    try:
        db = database.SessionLocal()
        yield db
    finally:
        if db:
            db.close()

@app.get("/", name="root")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Página de Inicio"})

@app.get("/medicamentos/", name="listar_todos_medicamentos")
async def listar_todos_medicamentos(request: Request, db: Session = Depends(get_db_session_fastapi)):
    medicamentos = crud.obtener_medicamentos(db, limit=1000)
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

# --- CRUD Medicamentos ---
@app.get("/medicamentos/nuevo/", name="crear_medicamento_form")
async def crear_medicamento_form(request: Request):
    return templates.TemplateResponse("form_medicamento.html", {
        "request": request,
        "form_title": "Añadir Nuevo Medicamento",
        "form_action": request.url_for("crear_medicamento_submit"),
        "medicamento": None,
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
    form_data_repop = {"nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja, "precio_por_caja_referencia": precio_por_caja_referencia}
    try:
        medicamento_data = schemas.MedicamentoCreate(
            nombre=nombre, marca=marca, unidades_por_caja=unidades_por_caja,
            precio_por_caja_referencia=precio_por_caja_referencia
        )
    except ValidationError as e:
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": form_data_repop, "errors": e.errors()
        }, status_code=422)

    db_medicamento_existente = crud.obtener_medicamento_por_nombre(db, nombre=medicamento_data.nombre)
    if db_medicamento_existente:
        errors.append({"loc": ["nombre"], "msg": "Ya existe un medicamento con este nombre."})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": form_data_repop, "errors": errors
        }, status_code=400)

    try:
        crud.crear_medicamento(db=db, nombre=medicamento_data.nombre, marca=medicamento_data.marca,
                               unidades_por_caja=medicamento_data.unidades_por_caja,
                               precio_referencia=medicamento_data.precio_por_caja_referencia)
        return RedirectResponse(url=request.url_for("listar_todos_medicamentos"), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al guardar el medicamento: {e}"})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": form_data_repop, "errors": errors
        }, status_code=500)

@app.get("/medicamentos/{medicamento_id}/editar/", name="editar_medicamento_form")
async def editar_medicamento_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado")
    return templates.TemplateResponse("form_medicamento.html", {
        "request": request, "form_title": f"Editar Medicamento: {medicamento.nombre}",
        "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
        "medicamento": medicamento, "errors": None
    })

@app.post("/medicamentos/{medicamento_id}/editar/", name="editar_medicamento_submit")
async def editar_medicamento_submit(
    request: Request, medicamento_id: int, nombre: str = Form(...),
    marca: Optional[str] = Form(None), unidades_por_caja: int = Form(...),
    precio_por_caja_referencia: Optional[float] = Form(None),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    medicamento_original = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento_original:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado para actualizar")

    form_data_repop = {"id": medicamento_id, "nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja, "precio_por_caja_referencia": precio_por_caja_referencia}

    try:
        medicamento_data_update = schemas.MedicamentoUpdate(
            nombre=nombre, marca=marca, unidades_por_caja=unidades_por_caja,
            precio_por_caja_referencia=precio_por_caja_referencia
        )
    except ValidationError as e:
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": form_data_repop, "errors": e.errors()
        }, status_code=422)

    if medicamento_data_update.nombre and medicamento_data_update.nombre.lower() != medicamento_original.nombre.lower():
        db_medicamento_existente = crud.obtener_medicamento_por_nombre(db, nombre=medicamento_data_update.nombre)
        if db_medicamento_existente and db_medicamento_existente.id != medicamento_id:
            errors.append({"loc": ["nombre"], "msg": "Ya existe otro medicamento con este nombre."})
            return templates.TemplateResponse("form_medicamento.html", {
                "request": request, "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
                "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
                "medicamento": form_data_repop, "errors": errors
            }, status_code=400)

    try:
        update_data_dict = medicamento_data_update.dict(exclude_unset=True)
        if marca == "": update_data_dict['marca'] = None
        if 'precio_por_caja_referencia' not in update_data_dict and precio_por_caja_referencia is None and medicamento_original.precio_por_caja_referencia is not None:
            update_data_dict['precio_por_caja_referencia'] = None
        if not update_data_dict:
             return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)
        crud.actualizar_medicamento(db, medicamento_id=medicamento_id, datos_actualizacion=update_data_dict)
        return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al actualizar el medicamento: {e}"})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": form_data_repop, "errors": errors
        }, status_code=500)

@app.get("/medicamentos/{medicamento_id}/eliminar/", name="eliminar_medicamento_confirm_form")
async def eliminar_medicamento_confirm_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail=f"Medicamento con ID {medicamento_id} no encontrado")
    return templates.TemplateResponse("confirmar_eliminacion_medicamento.html", {
        "request": request, "medicamento": medicamento, "title": f"Confirmar Eliminación: {medicamento.nombre}"
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
        "request": request, "medicamento": medicamento, "lotes": lotes,
        "stock_total": stock_total, "vencimiento_proximo": vencimiento_proximo,
        "today_date": py_date.today(), "title": f"Detalle: {medicamento.nombre}"
    })

# --- Rutas para Pedidos (Visualización y CRUD de encabezado) ---
@app.get("/pedidos/", name="listar_todos_pedidos")
async def listar_todos_pedidos(request: Request, db: Session = Depends(get_db_session_fastapi)):
    pedidos = crud.obtener_pedidos(db, limit=1000)
    pedidos_info = []
    for p in pedidos:
        costo_total = crud.calcular_costo_total_pedido(db, p.id)
        pedidos_info.append({"pedido": p, "costo_total": costo_total})
    return templates.TemplateResponse("lista_pedidos.html", {"request": request, "pedidos_info": pedidos_info, "title": "Lista de Pedidos"})

@app.get("/pedidos/nuevo/", name="crear_pedido_form")
async def crear_pedido_form(request: Request):
    from datetime import date as py_date
    return templates.TemplateResponse("form_pedido.html", {
        "request": request, "form_title": "Crear Nuevo Pedido",
        "form_action": request.url_for("crear_pedido_submit"), "pedido": None,
        "estados_posibles": list(schemas.EstadoPedidoEnum),
        "today_date_iso": py_date.today().isoformat(), "errors": None
    })

@app.post("/pedidos/nuevo/", name="crear_pedido_submit")
async def crear_pedido_submit(
    request: Request,
    fecha_pedido_str: Optional[str] = Form(None, alias="fecha_pedido"),
    proveedor: Optional[str] = Form(None),
    estado_str: str = Form(schemas.EstadoPedidoEnum.PENDIENTE.name, alias="estado"), # Recibido como string
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    from datetime import date as py_date
    fecha_pedido_obj: Optional[py_date] = None
    form_data_repop = {"proveedor": proveedor, "estado_str_form": estado_str, "fecha_pedido_str_form": fecha_pedido_str if fecha_pedido_str else py_date.today().isoformat()}

    if fecha_pedido_str:
        try:
            fecha_pedido_obj = py_date.fromisoformat(fecha_pedido_str)
        except ValueError:
            errors.append({"loc": ["fecha_pedido"], "msg": "Formato de fecha inválido. Use YYYY-MM-DD."})
    else:
        fecha_pedido_obj = py_date.today()

    if errors:
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": "Crear Nuevo Pedido",
            "form_action": request.url_for("crear_pedido_submit"),
            "pedido": form_data_repop,
            "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=422)

    try:
        estado_enum_val = schemas.EstadoPedidoEnum[estado_str.upper()] # Convertir string a Enum (usar .upper() para más robustez)
        pedido_data = schemas.PedidoCreate(fecha_pedido=fecha_pedido_obj, proveedor=proveedor, estado=estado_enum_val)
    except KeyError:
        errors.append({"loc": ["estado"], "msg": "Valor de estado no válido."})
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": "Crear Nuevo Pedido",
            "form_action": request.url_for("crear_pedido_submit"), "pedido": form_data_repop,
            "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=422)
    except ValidationError as e:
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": "Crear Nuevo Pedido",
            "form_action": request.url_for("crear_pedido_submit"), "pedido": form_data_repop,
            "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": py_date.today().isoformat(), "errors": e.errors()
        }, status_code=422)

    try:
        pedido = crud.crear_pedido(db=db, fecha_pedido=pedido_data.fecha_pedido,
                                   proveedor=pedido_data.proveedor, estado=pedido_data.estado)
        return RedirectResponse(url=request.url_for("detalle_pedido_ruta", pedido_id=pedido.id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al guardar el pedido: {e}"})
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": "Crear Nuevo Pedido",
            "form_action": request.url_for("crear_pedido_submit"), "pedido": form_data_repop,
            "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=500)

@app.get("/pedidos/{pedido_id}/editar/", name="editar_pedido_form")
async def editar_pedido_form(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID {pedido_id} no encontrado")
    from datetime import date as py_date
    return templates.TemplateResponse("form_pedido.html", {
        "request": request, "form_title": f"Editar Pedido #{pedido.id}",
        "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
        "pedido": pedido, "estados_posibles": list(schemas.EstadoPedidoEnum),
        "today_date_iso": pedido.fecha_pedido.isoformat() if pedido.fecha_pedido else py_date.today().isoformat(), "errors": None
    })

@app.post("/pedidos/{pedido_id}/editar/", name="editar_pedido_submit")
async def editar_pedido_submit(
    request: Request, pedido_id: int, fecha_pedido_str: str = Form(..., alias="fecha_pedido"),
    proveedor: Optional[str] = Form(None), estado_str: str = Form(..., alias="estado"),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    pedido_original = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido_original:
        raise HTTPException(status_code=404, detail=f"Pedido con ID {pedido_id} no encontrado para actualizar")

    from datetime import date as py_date
    fecha_pedido_obj: Optional[py_date] = None
    form_data_repop = {"id": pedido_id, "fecha_pedido_str_form": fecha_pedido_str, "proveedor": proveedor, "estado_str_form": estado_str}


    try:
        fecha_pedido_obj = py_date.fromisoformat(fecha_pedido_str)
    except ValueError:
        errors.append({"loc": ["fecha_pedido"], "msg": "Formato de fecha inválido. Use YYYY-MM-DD."})

    if errors:
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": f"Editar Pedido #{pedido_id}",
            "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
            "pedido": form_data_repop,
            "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": fecha_pedido_str,
            "errors": errors
        }, status_code=422)

    try:
        estado_enum_val = schemas.EstadoPedidoEnum[estado_str.upper()]
        pedido_data_update = schemas.PedidoUpdate(
            fecha_pedido=fecha_pedido_obj,
            proveedor=proveedor,
            estado=estado_enum_val
        )
    except KeyError:
        errors.append({"loc": ["estado"], "msg": "Valor de estado no válido."})
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": f"Editar Pedido #{pedido_id}",
            "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
            "pedido": form_data_repop,
            "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": fecha_pedido_str,
            "errors": errors
        }, status_code=422)
    except ValidationError as e:
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": f"Editar Pedido #{pedido_id}",
            "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
            "pedido": form_data_repop,
            "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": fecha_pedido_str,
            "errors": e.errors()
        }, status_code=422)

    try:
        update_data_dict = pedido_data_update.dict(exclude_unset=True)
        if proveedor == "":
            update_data_dict['proveedor'] = None
        elif proveedor is None and 'proveedor' not in update_data_dict and pedido_original.proveedor is not None:
             update_data_dict['proveedor'] = None

        if not update_data_dict:
            return RedirectResponse(url=request.url_for("detalle_pedido_ruta", pedido_id=pedido_id), status_code=303)

        crud.actualizar_pedido(db, pedido_id=pedido_id, datos_actualizacion=update_data_dict)
        return RedirectResponse(url=request.url_for("detalle_pedido_ruta", pedido_id=pedido_id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al actualizar el pedido: {e}"})
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": f"Editar Pedido #{pedido_id}",
            "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
            "pedido": form_data_repop,
            "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": fecha_pedido_str,
            "errors": errors
        }, status_code=500)

@app.get("/pedidos/{pedido_id}/eliminar/", name="eliminar_pedido_confirm_form")
async def eliminar_pedido_confirm_form(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID {pedido_id} no encontrado")
    return templates.TemplateResponse("confirmar_eliminacion_pedido.html", {"request": request, "pedido": pedido, "title": f"Confirmar Eliminación Pedido #{pedido.id}"})

@app.post("/pedidos/{pedido_id}/eliminar/", name="eliminar_pedido_submit")
async def eliminar_pedido_submit(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    pedido_a_eliminar = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido_a_eliminar:
        raise HTTPException(status_code=404, detail=f"Pedido con ID {pedido_id} no encontrado para eliminar")
    try:
        crud.eliminar_pedido(db, pedido_id=pedido_id)
        return RedirectResponse(url=request.url_for("listar_todos_pedidos"), status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el pedido: {e}")

# Esta ruta debe ir DESPUÉS de las rutas CRUD de pedidos para evitar conflictos
@app.get("/pedidos/{pedido_id}/", name="detalle_pedido_ruta") # Renombrada para evitar conflicto con la variable 'detalle_pedido'
async def detalle_pedido_ruta(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        return templates.TemplateResponse("error_404.html", {"request": request, "detail": f"Pedido con ID {pedido_id} no encontrado"}, status_code=404)
    detalles_pedido = crud.obtener_detalles_por_pedido(db, pedido_id=pedido_id)
    costo_total = crud.calcular_costo_total_pedido(db, pedido_id=pedido_id)
    return templates.TemplateResponse("detalle_pedido.html", {
        "request": request, "pedido": pedido, "detalles_pedido": detalles_pedido,
        "costo_total": costo_total, "title": f"Detalle Pedido #{pedido.id}"
    })

if __name__ == "__main__":
    print("Para ejecutar esta aplicación web, use el comando:")
    print("uvicorn gestion_medicamentos.main_web:app --reload --port 8000")
    print(f"Asegúrese de estar en el directorio raíz del repositorio ('{os.path.dirname(current_dir)}') al ejecutar uvicorn.")

[end of gestion_medicamentos/main_web.py]
