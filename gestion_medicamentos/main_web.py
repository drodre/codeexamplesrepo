# Archivo principal para la aplicación web FastAPI del Gestor de Medicamentos.

import os
import sys
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import ValidationError
from typing import Optional, List
from datetime import date as py_date # Renombrar para evitar conflicto con models.Date

# Añadir el directorio de la aplicación al sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import crud, models, database, schemas
except ImportError as e:
    print(f"Error importando módulos de app: {e}")
    print(f"sys.path actual: {sys.path}")
    raise

# --- Configuración de Autenticación HTTP Basic ---
import secrets
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

# !! ADVERTENCIA: Estas son credenciales de ejemplo. !!
# !! NO USAR EN PRODUCCIÓN. Cambiar por un método seguro de gestión de credenciales. !!
CORRECT_USERNAME = "admin"
CORRECT_PASSWORD = "securepassword123" # Cambiar esto en un entorno real

async def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = CORRECT_USERNAME.encode("utf8")
    is_correct_username = secrets.compare_digest(current_username_bytes, correct_username_bytes)

    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = CORRECT_PASSWORD.encode("utf8")
    is_correct_password = secrets.compare_digest(current_password_bytes, correct_password_bytes)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Aplicar autenticación a toda la aplicación
app = FastAPI(
    title="Gestor de Medicamentos Caseros - Web",
    version="0.1.0",
    dependencies=[Depends(verify_credentials)] # Proteger todas las rutas
)

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "web", "templates")
templates = Jinja2Templates(directory=templates_dir)
templates.env.globals['py_date'] = py_date # Hacer py_date (datetime.date) accesible en todas las plantillas

# --- Dependencia de Sesión de BD ---
def get_db_session_fastapi():
    db = None
    try:
        db = database.SessionLocal()
        yield db
    finally:
        if db:
            db.close()

# --- Rutas Principales ---
@app.get("/", name="root")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Página de Inicio"})

# --- Rutas para Medicamentos ---
@app.get("/medicamentos/", name="listar_todos_medicamentos")
async def listar_todos_medicamentos(request: Request, db: Session = Depends(get_db_session_fastapi)):
    medicamentos = crud.obtener_medicamentos(db, limit=1000)
    medicamentos_info = []
    for med in medicamentos:
        stock_total = crud.calcular_stock_total_unidades(db, med.id)
        vencimiento_proximo = crud.calcular_fecha_vencimiento_proxima(db, med.id)
        precio_por_unidad = None
        if med.precio_por_caja_referencia is not None and med.unidades_por_caja > 0:
            precio_por_unidad = med.precio_por_caja_referencia / med.unidades_por_caja
        medicamentos_info.append({
            "medicamento": med,
            "stock_total": stock_total,
            "vencimiento_proximo": vencimiento_proximo,
            "precio_por_unidad": precio_por_unidad
        })
    return templates.TemplateResponse("lista_medicamentos.html", {
        "request": request, "medicamentos_info": medicamentos_info, "title": "Lista de Medicamentos"
    })

@app.get("/medicamentos/nuevo/", name="crear_medicamento_form")
async def crear_medicamento_form(request: Request):
    return templates.TemplateResponse("form_medicamento.html", {
        "request": request, "form_title": "Añadir Nuevo Medicamento",
        "form_action": request.url_for("crear_medicamento_submit"),
        "medicamento": None, "errors": None
    })

@app.post("/medicamentos/nuevo/", name="crear_medicamento_submit")
async def crear_medicamento_submit(
    request: Request, nombre: str = Form(...), marca: Optional[str] = Form(None),
    unidades_por_caja: int = Form(...), precio_por_caja_referencia: Optional[float] = Form(None),
    esta_activo_sentinel: Optional[str] = Form(None), esta_activo: Optional[str] = Form(None),
    vencimiento_receta_str: Optional[str] = Form(None, alias="vencimiento_receta"),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    esta_activo_bool = True if esta_activo == "true" else False
    vencimiento_receta_obj: Optional[py_date] = None

    if vencimiento_receta_str:
        try:
            vencimiento_receta_obj = py_date.fromisoformat(vencimiento_receta_str)
        except ValueError:
            errors.append({"loc": ["vencimiento_receta"], "msg": "Formato de fecha de vencimiento de receta inválido. Use YYYY-MM-DD."})

    form_data_repop = {
        "nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja,
        "precio_por_caja_referencia": precio_por_caja_referencia,
        "esta_activo": esta_activo_bool,
        "vencimiento_receta": vencimiento_receta_obj # Para repopular, usar el objeto o None
    }

    if errors: # Si hubo error en la conversión de fecha, retornar antes de validar con Pydantic
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": form_data_repop, "errors": errors # form_data_repop ya tiene la fecha como objeto si fue válida
        }, status_code=422)

    try:
        medicamento_dict_for_schema = {
            "nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja,
            "precio_por_caja_referencia": precio_por_caja_referencia,
            "esta_activo": esta_activo_bool,
            "vencimiento_receta": vencimiento_receta_obj
        }
        medicamento_data = schemas.MedicamentoCreate(**medicamento_dict_for_schema)

    except ValidationError as e:
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": form_data_repop, "errors": e.errors()
        }, status_code=422)

    if crud.obtener_medicamento_por_nombre(db, nombre=medicamento_data.nombre):
        errors.append({"loc": ["nombre"], "msg": "Ya existe un medicamento con este nombre."})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": form_data_repop, "errors": errors
        }, status_code=400)

    try:
        # Pasar explícitamente todos los campos a la función CRUD
        crud.crear_medicamento(db=db, nombre=medicamento_data.nombre, marca=medicamento_data.marca,
                               unidades_por_caja=medicamento_data.unidades_por_caja,
                               precio_por_caja_referencia=medicamento_data.precio_por_caja_referencia,
                               esta_activo=medicamento_data.esta_activo,
                               vencimiento_receta=medicamento_data.vencimiento_receta)
        return RedirectResponse(url=request.url_for("listar_todos_medicamentos"), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado: {e}"})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": "Añadir Nuevo Medicamento",
            "form_action": request.url_for("crear_medicamento_submit"),
            "medicamento": form_data_repop, "errors": errors
        }, status_code=500)

@app.get("/medicamentos/{medicamento_id}/editar/", name="editar_medicamento_form")
async def editar_medicamento_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
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
    esta_activo_sentinel: Optional[str] = Form(None), esta_activo: Optional[str] = Form(None),
    vencimiento_receta_str: Optional[str] = Form(None, alias="vencimiento_receta"),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    medicamento_original = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento_original:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado para actualizar")

    esta_activo_bool = True if esta_activo == "true" else False
    vencimiento_receta_obj: Optional[py_date] = None

    if vencimiento_receta_str: # Si se envía algo (incluso vacío), intentar convertir
        try:
            vencimiento_receta_obj = py_date.fromisoformat(vencimiento_receta_str)
        except ValueError:
            # No añadir error aquí si el string está vacío, significa borrar la fecha
            if vencimiento_receta_str.strip() != "":
                errors.append({"loc": ["vencimiento_receta"], "msg": "Formato de fecha de vencimiento de receta inválido. Use YYYY-MM-DD."})
    # Si vencimiento_receta_str es None o un string vacío, vencimiento_receta_obj será None, lo que es correcto para borrar la fecha.


    form_data_repop = {
        "id": medicamento_id, "nombre": nombre, "marca": marca,
        "unidades_por_caja": unidades_por_caja,
        "precio_por_caja_referencia": precio_por_caja_referencia,
        "esta_activo": esta_activo_bool,
        "vencimiento_receta": vencimiento_receta_obj # Usar el objeto para repopular
    }

    if errors: # Error de formato de fecha
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": form_data_repop, "errors": errors
        }, status_code=422)

    try:
        medicamento_dict_for_schema = {
            "nombre": nombre, "marca": marca, "unidades_por_caja": unidades_por_caja,
            "precio_por_caja_referencia": precio_por_caja_referencia,
            "esta_activo": esta_activo_bool,
            "vencimiento_receta": vencimiento_receta_obj
        }
        medicamento_data_update = schemas.MedicamentoUpdate(**medicamento_dict_for_schema)

    except ValidationError as e: # Otros errores de Pydantic
        # Repopular con el medicamento original para el campo de fecha si la conversión falló antes y no se llegó aquí
        # o si el error de Pydantic es sobre otro campo.
        # form_data_repop ya tiene el valor correcto si la fecha se procesó.
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": form_data_repop, "errors": e.errors()
        }, status_code=422)

    if nombre.lower() != medicamento_original.nombre.lower():
        db_medicamento_existente = crud.obtener_medicamento_por_nombre(db, nombre=nombre)
        if db_medicamento_existente and db_medicamento_existente.id != medicamento_id:
            errors.append({"loc": ["nombre"], "msg": "Ya existe otro medicamento con este nombre."})
            return templates.TemplateResponse("form_medicamento.html", {
                "request": request, "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
                "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
                "medicamento": form_data_repop, "errors": errors
            }, status_code=400)

    try:
        # Construir el diccionario de actualización solo con los campos que realmente se quieren cambiar.
        # El schema MedicamentoUpdate ya tiene esta_activo como Optional.
        update_data_dict = medicamento_data_update.dict(exclude_unset=True) # exclude_unset es clave aquí

        # Ajustes manuales si es necesario (como el manejo de string vacío para marca que ya existía)
        if marca == "": update_data_dict['marca'] = None
        if 'precio_por_caja_referencia' not in update_data_dict and precio_por_caja_referencia is None and medicamento_original.precio_por_caja_referencia is not None:
            update_data_dict['precio_por_caja_referencia'] = None

        # Importante: Pydantic con exclude_unset=True no incluirá `esta_activo` ni `vencimiento_receta`
        # si sus valores son los default (None en MedicamentoUpdate).
        # Pero nosotros queremos que se actualicen según el form (True/False para activo, y fecha o None para receta).
        # Los valores ya están correctos en medicamento_data_update gracias a la creación del schema.
        # El método .dict() de Pydantic es el que decide qué incluir basado en exclude_unset, etc.
        # Para asegurar que estos campos se actualicen incluso si se setean a su valor "default" en el schema Update (como None),
        # los añadimos explícitamente al diccionario si fueron proveídos (o si su valor es diferente al original).

        update_data_dict = medicamento_data_update.dict(exclude_none=True) # exclude_none para campos que son None en el schema de update
                                                                        # pero que queremos pasar a la BD como None (para borrar la fecha por ej.)
                                                                        # No, mejor usar exclude_unset y añadir manualmente.

        update_data_dict = medicamento_data_update.dict(exclude_unset=True)

        # Asegurar que esta_activo siempre se considere para la actualización
        update_data_dict['esta_activo'] = esta_activo_bool

        # Manejar vencimiento_receta: si se envió un string vacío, vencimiento_receta_obj es None,
        # y queremos que se guarde None en la BD. Si se envió una fecha válida, se guarda.
        # Si no se envió nada para vencimiento_receta_str (es decir, el campo no estaba en el form o no se tocó),
        # entonces vencimiento_receta_obj es None, y Pydantic (con exclude_unset) no lo incluiría.
        # Pero si el usuario borró la fecha (enviando un string vacío), queremos pasar None.
        if vencimiento_receta_str is not None: # Indica que el campo fue enviado, incluso si vacío
            update_data_dict['vencimiento_receta'] = vencimiento_receta_obj
        # Si vencimiento_receta_str es None (no se envió), y el original tenía fecha, no se actualiza.
        # Si el original no tenía y no se envió, no se actualiza (queda None).
        # Esto es un poco complejo. Simplifiquemos: siempre pasar el valor de vencimiento_receta_obj
        # que ya hemos determinado (puede ser una fecha o None).
        update_data_dict['vencimiento_receta'] = vencimiento_receta_obj


        # Comprobar si hay cambios reales antes de hacer el update
        if not update_data_dict: # Si el diccionario está vacío después de exclude_unset y nuestras adiciones
             return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)

        # Lógica más precisa para "no cambios":
        # Compara cada campo en update_data_dict con el original.
        # Si todos los campos que se van a actualizar son iguales a los originales, entonces no hay cambio.
        no_cambios_reales = True
        if not update_data_dict: # Si está vacío, no hay cambios
            no_cambios_reales = True
        else:
            for key, value in update_data_dict.items():
                original_value = getattr(medicamento_original, key)
                if key == 'vencimiento_receta' and isinstance(original_value, py_date) and isinstance(value, str):
                    # Comparar fechas si el valor del form es string (no debería pasar si la conversión fue ok)
                     try:
                         value_date = py_date.fromisoformat(value)
                         if original_value != value_date:
                             no_cambios_reales = False; break
                     except ValueError:
                         no_cambios_reales = False; break # Formato inválido, es un cambio (erróneo)
                elif original_value != value:
                    no_cambios_reales = False; break

        if no_cambios_reales:
            return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)

        crud.actualizar_medicamento(db, medicamento_id=medicamento_id, datos_actualizacion=update_data_dict)
        return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado: {e}"})
        return templates.TemplateResponse("form_medicamento.html", {
            "request": request, "form_title": f"Editar Medicamento: {medicamento_original.nombre}",
            "form_action": request.url_for("editar_medicamento_submit", medicamento_id=medicamento_id),
            "medicamento": form_data_repop, "errors": errors
        }, status_code=500)

@app.get("/medicamentos/{medicamento_id}/eliminar/", name="eliminar_medicamento_confirm_form")
async def eliminar_medicamento_confirm_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado")
    return templates.TemplateResponse("confirmar_eliminacion_medicamento.html", {
        "request": request, "medicamento": medicamento, "title": f"Confirmar Eliminación: {medicamento.nombre}"
    })

@app.post("/medicamentos/{medicamento_id}/eliminar/", name="eliminar_medicamento_submit")
async def eliminar_medicamento_submit(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    if not crud.obtener_medicamento(db, medicamento_id=medicamento_id):
        raise HTTPException(status_code=404, detail="Medicamento no encontrado para eliminar")
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
    precio_por_unidad = None
    if medicamento.precio_por_caja_referencia is not None and medicamento.unidades_por_caja > 0:
        precio_por_unidad = medicamento.precio_por_caja_referencia / medicamento.unidades_por_caja

    return templates.TemplateResponse("detalle_medicamento.html", {
        "request": request, "medicamento": medicamento, "lotes": lotes,
        "stock_total": stock_total, "vencimiento_proximo": vencimiento_proximo,
        "precio_por_unidad": precio_por_unidad,
        "today_date": py_date.today(), "title": f"Detalle: {medicamento.nombre}"
    })

# --- Rutas para Pedidos ---
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
    return templates.TemplateResponse("form_pedido.html", {
        "request": request, "form_title": "Crear Nuevo Pedido",
        "form_action": request.url_for("crear_pedido_submit"), "pedido": None,
        "estados_posibles": list(schemas.EstadoPedidoEnum),
        "today_date_iso": py_date.today().isoformat(), "errors": None
    })

@app.post("/pedidos/nuevo/", name="crear_pedido_submit")
async def crear_pedido_submit(
    request: Request, fecha_pedido_str: Optional[str] = Form(None, alias="fecha_pedido"),
    proveedor: Optional[str] = Form(None), estado_str: str = Form(schemas.EstadoPedidoEnum.PENDIENTE.name, alias="estado"),
    db: Session = Depends(get_db_session_fastapi)
):
    errors = []
    fecha_pedido_obj: Optional[py_date] = None
    form_data_repop = {"proveedor": proveedor, "estado_str_form": estado_str, "fecha_pedido_str_form": fecha_pedido_str if fecha_pedido_str else py_date.today().isoformat()}

    if fecha_pedido_str:
        try: fecha_pedido_obj = py_date.fromisoformat(fecha_pedido_str)
        except ValueError: errors.append({"loc": ["fecha_pedido"], "msg": "Formato de fecha inválido. Use YYYY-MM-DD."})
    else: fecha_pedido_obj = py_date.today()

    if errors:
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": "Crear Nuevo Pedido", "form_action": request.url_for("crear_pedido_submit"),
            "pedido": form_data_repop, "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=422)

    try:
        estado_enum_val = schemas.EstadoPedidoEnum[estado_str.upper()]
        pedido_data = schemas.PedidoCreate(fecha_pedido=fecha_pedido_obj, proveedor=proveedor, estado=estado_enum_val)
    except KeyError:
        errors.append({"loc": ["estado"], "msg": "Valor de estado no válido."})
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": "Crear Nuevo Pedido", "form_action": request.url_for("crear_pedido_submit"),
            "pedido": form_data_repop, "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=422)
    except ValidationError as e:
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": "Crear Nuevo Pedido", "form_action": request.url_for("crear_pedido_submit"),
            "pedido": form_data_repop, "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": py_date.today().isoformat(), "errors": e.errors()
        }, status_code=422)

    try:
        pedido = crud.crear_pedido(db=db, fecha_pedido=pedido_data.fecha_pedido,
                                   proveedor=pedido_data.proveedor, estado=pedido_data.estado)
        return RedirectResponse(url=request.url_for("detalle_pedido_ruta", pedido_id=pedido.id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado: {e}"})
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": "Crear Nuevo Pedido", "form_action": request.url_for("crear_pedido_submit"),
            "pedido": form_data_repop, "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=500)

@app.get("/pedidos/{pedido_id}/editar/", name="editar_pedido_form")
async def editar_pedido_form(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
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
        raise HTTPException(status_code=404, detail="Pedido no encontrado para actualizar")

    fecha_pedido_obj: Optional[py_date] = None
    form_data_repop = {"id": pedido_id, "fecha_pedido_str_form": fecha_pedido_str, "proveedor": proveedor, "estado_str_form": estado_str}

    try: fecha_pedido_obj = py_date.fromisoformat(fecha_pedido_str)
    except ValueError: errors.append({"loc": ["fecha_pedido"], "msg": "Formato de fecha inválido. Use YYYY-MM-DD."})

    if errors:
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": f"Editar Pedido #{pedido_id}",
            "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
            "pedido": form_data_repop, "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": fecha_pedido_str, "errors": errors
        }, status_code=422)

    try:
        estado_enum_val = schemas.EstadoPedidoEnum[estado_str.upper()]
        pedido_data_update = schemas.PedidoUpdate(fecha_pedido=fecha_pedido_obj, proveedor=proveedor, estado=estado_enum_val)
    except KeyError:
        errors.append({"loc": ["estado"], "msg": "Valor de estado no válido."})
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": f"Editar Pedido #{pedido_id}",
            "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
            "pedido": form_data_repop, "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": fecha_pedido_str, "errors": errors
        }, status_code=422)
    except ValidationError as e:
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": f"Editar Pedido #{pedido_id}",
            "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
            "pedido": form_data_repop, "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": fecha_pedido_str, "errors": e.errors()
        }, status_code=422)

    try:
        update_data_dict = pedido_data_update.dict(exclude_unset=True)
        if proveedor == "": update_data_dict['proveedor'] = None
        elif proveedor is None and 'proveedor' not in update_data_dict and pedido_original.proveedor is not None:
             update_data_dict['proveedor'] = None

        if not update_data_dict:
            return RedirectResponse(url=request.url_for("detalle_pedido_ruta", pedido_id=pedido_id), status_code=303)
        crud.actualizar_pedido(db, pedido_id=pedido_id, datos_actualizacion=update_data_dict)
        return RedirectResponse(url=request.url_for("detalle_pedido_ruta", pedido_id=pedido_id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado: {e}"})
        return templates.TemplateResponse("form_pedido.html", {
            "request": request, "form_title": f"Editar Pedido #{pedido_id}",
            "form_action": request.url_for("editar_pedido_submit", pedido_id=pedido_id),
            "pedido": form_data_repop, "estados_posibles": list(schemas.EstadoPedidoEnum),
            "today_date_iso": fecha_pedido_str, "errors": errors
        }, status_code=500)

@app.get("/pedidos/{pedido_id}/eliminar/", name="eliminar_pedido_confirm_form")
async def eliminar_pedido_confirm_form(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return templates.TemplateResponse("confirmar_eliminacion_pedido.html", {"request": request, "pedido": pedido, "title": f"Confirmar Eliminación Pedido #{pedido.id}"})

@app.post("/pedidos/{pedido_id}/eliminar/", name="eliminar_pedido_submit")
async def eliminar_pedido_submit(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    if not crud.obtener_pedido(db, pedido_id=pedido_id):
        raise HTTPException(status_code=404, detail="Pedido no encontrado para eliminar")
    try:
        crud.eliminar_pedido(db, pedido_id=pedido_id)
        return RedirectResponse(url=request.url_for("listar_todos_pedidos"), status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el pedido: {e}")

# --- CRUD DetallesPedido (Ítems de Pedido) ---

@app.get("/pedidos/{pedido_id}/items/nuevo/", name="crear_detalle_pedido_form")
async def crear_detalle_pedido_form(request: Request, pedido_id: int, db: Session = Depends(get_db_session_fastapi)):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID {pedido_id} no encontrado.")

    if pedido.estado != models.EstadoPedido.PENDIENTE:
        raise HTTPException(status_code=403, detail=f"No se pueden añadir ítems a un pedido que no esté en estado '{models.EstadoPedido.PENDIENTE.value}'. Estado actual: {pedido.estado.value}")

    medicamentos_disponibles = crud.obtener_medicamentos(db, limit=1000)

    return templates.TemplateResponse("form_detalle_pedido.html", {
        "request": request,
        "form_title": f"Añadir Ítem al Pedido #{pedido.id}",
        "form_action": request.url_for("crear_detalle_pedido_submit", pedido_id=pedido_id),
        "pedido_id": pedido_id,
        "medicamentos_disponibles": medicamentos_disponibles,
        "errors": None,
        "detalle_data": None
    })

@app.post("/pedidos/{pedido_id}/items/nuevo/", name="crear_detalle_pedido_submit")
async def crear_detalle_pedido_submit(
    request: Request,
    pedido_id: int,
    medicamento_id: int = Form(...),
    cantidad_cajas_pedidas: int = Form(...),
    precio_unitario_compra_caja: Optional[float] = Form(None),
    db: Session = Depends(get_db_session_fastapi)
):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID {pedido_id} no encontrado.")
    if pedido.estado != models.EstadoPedido.PENDIENTE:
        raise HTTPException(status_code=403, detail="No se pueden añadir ítems a este pedido (estado no es Pendiente).")

    errors = []
    form_data_repop = {
        "medicamento_id": medicamento_id,
        "cantidad_cajas_pedidas": cantidad_cajas_pedidas,
        "precio_unitario_compra_caja": precio_unitario_compra_caja
    }

    if not crud.obtener_medicamento(db, medicamento_id=medicamento_id):
        errors.append({"loc": ["medicamento_id"], "msg": "El medicamento seleccionado no es válido."})

    if cantidad_cajas_pedidas <= 0:
         errors.append({"loc": ["cantidad_cajas_pedidas"], "msg": "La cantidad de cajas debe ser positiva."})

    if errors:
        medicamentos_disponibles = crud.obtener_medicamentos(db, limit=1000)
        return templates.TemplateResponse("form_detalle_pedido.html", {
            "request": request, "form_title": f"Añadir Ítem al Pedido #{pedido_id}",
            "form_action": request.url_for("crear_detalle_pedido_submit", pedido_id=pedido_id),
            "pedido_id": pedido_id, "medicamentos_disponibles": medicamentos_disponibles,
            "detalle_data": form_data_repop,
            "errors": errors
        }, status_code=422)

    try:
        detalle_data_schema = schemas.DetallePedidoCreate(**form_data_repop)
    except ValidationError as e:
        medicamentos_disponibles = crud.obtener_medicamentos(db, limit=1000)
        return templates.TemplateResponse("form_detalle_pedido.html", {
            "request": request, "form_title": f"Añadir Ítem al Pedido #{pedido_id}",
            "form_action": request.url_for("crear_detalle_pedido_submit", pedido_id=pedido_id),
            "pedido_id": pedido_id, "medicamentos_disponibles": medicamentos_disponibles,
            "detalle_data": form_data_repop,
            "errors": e.errors()
        }, status_code=422)

    try:
        crud.agregar_detalle_pedido(
            db=db, pedido_id=pedido_id, medicamento_id=detalle_data_schema.medicamento_id,
            cantidad_cajas_pedidas=detalle_data_schema.cantidad_cajas_pedidas,
            precio_unitario_compra_caja=detalle_data_schema.precio_unitario_compra_caja
        )
        return RedirectResponse(url=request.url_for("detalle_pedido_ruta", pedido_id=pedido_id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al añadir el ítem: {e}"})
        medicamentos_disponibles = crud.obtener_medicamentos(db, limit=1000)
        return templates.TemplateResponse("form_detalle_pedido.html", {
            "request": request, "form_title": f"Añadir Ítem al Pedido #{pedido_id}",
            "form_action": request.url_for("crear_detalle_pedido_submit", pedido_id=pedido_id),
            "pedido_id": pedido_id, "medicamentos_disponibles": medicamentos_disponibles,
            "detalle_data": form_data_repop,
            "errors": errors
        }, status_code=500)

@app.post("/pedidos/{pedido_id}/items/{detalle_id}/eliminar/", name="eliminar_detalle_pedido_submit")
async def eliminar_detalle_pedido_submit(
    request: Request,
    pedido_id: int,
    detalle_id: int,
    db: Session = Depends(get_db_session_fastapi)
):
    pedido = crud.obtener_pedido(db, pedido_id=pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail=f"Pedido con ID {pedido_id} no encontrado.")
    if pedido.estado != models.EstadoPedido.PENDIENTE:
        # Idealmente, este chequeo también debería estar en la lógica de la plantilla para no mostrar el botón.
        raise HTTPException(status_code=403, detail="No se pueden eliminar ítems de este pedido (estado no es Pendiente).")

    detalle_a_eliminar = crud.obtener_detalle_pedido(db, detalle_id=detalle_id)
    if not detalle_a_eliminar or detalle_a_eliminar.pedido_id != pedido_id:
        raise HTTPException(status_code=404, detail=f"Ítem de pedido con ID {detalle_id} no encontrado o no pertenece al pedido {pedido_id}.")

    try:
        eliminado = crud.eliminar_detalle_pedido(db, detalle_id=detalle_id)
        if not eliminado:
            raise HTTPException(status_code=500, detail=f"No se pudo eliminar el ítem de pedido ID {detalle_id}.")

        return RedirectResponse(url=request.url_for("detalle_pedido_ruta", pedido_id=pedido_id), status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado al eliminar el ítem del pedido: {e}")


# --- CRUD Lotes de Stock ---
@app.get("/medicamentos/{medicamento_id}/lotes/nuevo/", name="crear_lote_form")
async def crear_lote_form(request: Request, medicamento_id: int, db: Session = Depends(get_db_session_fastapi)):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        raise HTTPException(status_code=404, detail="Medicamento no encontrado para añadir lote.")

    return templates.TemplateResponse("form_lote.html", {
        "request": request,
        "form_title": f"Añadir Nuevo Lote para: {medicamento.nombre}",
        "form_action": request.url_for("crear_lote_submit", medicamento_id=medicamento_id),
        "medicamento_info": medicamento, # Para mostrar info del medicamento y pre-rellenar unidades/caja
        "lote": None, # No hay lote existente
        "today_date_iso": py_date.today().isoformat(),
        "errors": None
    })

@app.post("/medicamentos/{medicamento_id}/lotes/nuevo/", name="crear_lote_submit")
async def crear_lote_submit(
    request: Request,
    medicamento_id: int,
    cantidad_cajas: int = Form(...),
    unidades_por_caja_lote: int = Form(...),
    fecha_compra_lote_str: Optional[str] = Form(None, alias="fecha_compra_lote"),
    fecha_vencimiento_lote_str: str = Form(..., alias="fecha_vencimiento_lote"),
    precio_compra_lote_por_caja: Optional[float] = Form(None),
    db: Session = Depends(get_db_session_fastapi)
):
    medicamento = crud.obtener_medicamento(db, medicamento_id=medicamento_id)
    if not medicamento:
        # Esto no debería ocurrir si el GET funcionó, pero es una salvaguarda.
        raise HTTPException(status_code=404, detail="Medicamento no encontrado para añadir lote.")

    errors = []
    # Para repopular el formulario en caso de error
    form_data_repop = {
        "cantidad_cajas": cantidad_cajas, "unidades_por_caja_lote": unidades_por_caja_lote,
        "fecha_compra_lote_str_form": fecha_compra_lote_str if fecha_compra_lote_str else py_date.today().isoformat(), # Para repopular input date
        "fecha_vencimiento_lote_str_form": fecha_vencimiento_lote_str,
        "precio_compra_lote_por_caja": precio_compra_lote_por_caja
    }

    fecha_compra_obj: Optional[py_date] = None
    if fecha_compra_lote_str:
        try: fecha_compra_obj = py_date.fromisoformat(fecha_compra_lote_str)
        except ValueError: errors.append({"loc": ["fecha_compra_lote"], "msg": "Formato de fecha de compra inválido. Use YYYY-MM-DD."})
    else: # Si no se provee, el modelo SQL usará la fecha actual. Pydantic schema lo tiene como Optional.
        fecha_compra_obj = None # Se pasará None al schema, que lo permitirá.

    fecha_vencimiento_obj: Optional[py_date] = None
    if fecha_vencimiento_lote_str:
        try: fecha_vencimiento_obj = py_date.fromisoformat(fecha_vencimiento_lote_str)
        except ValueError: errors.append({"loc": ["fecha_vencimiento_lote"], "msg": "Formato de fecha de vencimiento inválido. Use YYYY-MM-DD."})
    else: # Fecha de vencimiento es obligatoria
        errors.append({"loc": ["fecha_vencimiento_lote"], "msg": "La fecha de vencimiento es obligatoria."})

    if cantidad_cajas <=0: errors.append({"loc": ["cantidad_cajas"], "msg": "Cantidad de cajas debe ser positiva."})
    if unidades_por_caja_lote <=0: errors.append({"loc": ["unidades_por_caja_lote"], "msg": "Unidades por caja debe ser positivo."})


    if errors:
        return templates.TemplateResponse("form_lote.html", {
            "request": request, "form_title": f"Añadir Nuevo Lote para: {medicamento.nombre}",
            "form_action": request.url_for("crear_lote_submit", medicamento_id=medicamento_id),
            "medicamento_info": medicamento, "lote": form_data_repop,
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=422)

    try:
        lote_data = schemas.LoteStockCreate(
            cantidad_cajas=cantidad_cajas, unidades_por_caja_lote=unidades_por_caja_lote,
            fecha_compra_lote=fecha_compra_obj, # Puede ser None, el modelo SQL se encarga del default
            fecha_vencimiento_lote=fecha_vencimiento_obj, # Debe ser un objeto date aquí
            precio_compra_lote_por_caja=precio_compra_lote_por_caja
            # medicamento_id se pasa directamente a la función crud
        )
    except ValidationError as e:
        return templates.TemplateResponse("form_lote.html", {
            "request": request, "form_title": f"Añadir Nuevo Lote para: {medicamento.nombre}",
            "form_action": request.url_for("crear_lote_submit", medicamento_id=medicamento_id),
            "medicamento_info": medicamento, "lote": form_data_repop,
            "today_date_iso": py_date.today().isoformat(), "errors": e.errors()
        }, status_code=422)

    try:
        crud.agregar_lote_stock(
            db=db, medicamento_id=medicamento_id,
            cantidad_cajas=lote_data.cantidad_cajas,
            unidades_por_caja_lote=lote_data.unidades_por_caja_lote,
            fecha_vencimiento_lote=lote_data.fecha_vencimiento_lote, # Esta es obligatoria
            fecha_compra_lote=lote_data.fecha_compra_lote, # Opcional, crud se encarga si es None
            precio_compra_lote_por_caja=lote_data.precio_compra_lote_por_caja
        )
        return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id), status_code=303)
    except ValueError as ve: # Por ejemplo, si el medicamento_id no existe en la función crud
        errors.append({"loc": ["medicamento_id"], "msg": str(ve)})
        return templates.TemplateResponse("form_lote.html", {
            "request": request, "form_title": f"Añadir Nuevo Lote para: {medicamento.nombre}",
            "form_action": request.url_for("crear_lote_submit", medicamento_id=medicamento_id),
            "medicamento_info": medicamento, "lote": form_data_repop,
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=400)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al guardar el lote: {e}"})
        return templates.TemplateResponse("form_lote.html", {
            "request": request, "form_title": f"Añadir Nuevo Lote para: {medicamento.nombre}",
            "form_action": request.url_for("crear_lote_submit", medicamento_id=medicamento_id),
            "medicamento_info": medicamento, "lote": form_data_repop,
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=500)

@app.get("/lotes/{lote_id}/editar/", name="editar_lote_form")
async def editar_lote_form(request: Request, lote_id: int, db: Session = Depends(get_db_session_fastapi)):
    lote = crud.obtener_lote_stock(db, lote_id=lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado.")

    medicamento = crud.obtener_medicamento(db, medicamento_id=lote.medicamento_id) # Necesario para el título y 'Cancelar'
    if not medicamento: # Muy improbable si el lote existe, pero por seguridad
        raise HTTPException(status_code=404, detail="Medicamento asociado al lote no encontrado.")

    return templates.TemplateResponse("form_lote.html", {
        "request": request,
        "form_title": f"Editar Lote #{lote.id} para: {medicamento.nombre}",
        "form_action": request.url_for("editar_lote_submit", lote_id=lote_id),
        "medicamento_info": medicamento, # Para el contexto de unidades/caja y el enlace de cancelar
        "lote": lote, # Pasar el lote existente para pre-rellenar
        "today_date_iso": py_date.today().isoformat(), # Aunque las fechas del lote deberían existir
        "errors": None
    })

@app.post("/lotes/{lote_id}/editar/", name="editar_lote_submit")
async def editar_lote_submit(
    request: Request,
    lote_id: int,
    cantidad_cajas: int = Form(...),
    unidades_por_caja_lote: int = Form(...),
    fecha_compra_lote_str: str = Form(..., alias="fecha_compra_lote"), # La fecha de compra es obligatoria en el form de edición
    fecha_vencimiento_lote_str: str = Form(..., alias="fecha_vencimiento_lote"),
    precio_compra_lote_por_caja: Optional[float] = Form(None),
    db: Session = Depends(get_db_session_fastapi)
):
    lote_original = crud.obtener_lote_stock(db, lote_id=lote_id)
    if not lote_original:
        raise HTTPException(status_code=404, detail="Lote no encontrado para actualizar.")

    medicamento = crud.obtener_medicamento(db, medicamento_id=lote_original.medicamento_id) # Para re-renderizar si hay error

    errors = []
    form_data_repop = { # Para repopular el formulario
        "id": lote_id, # Para que la plantilla sepa que es edición
        "cantidad_cajas": cantidad_cajas, "unidades_por_caja_lote": unidades_por_caja_lote,
        "fecha_compra_lote": fecha_compra_lote_str, # Pasar el string original
        "fecha_vencimiento_lote": fecha_vencimiento_lote_str,
        "precio_compra_lote_por_caja": precio_compra_lote_por_caja
    }

    fecha_compra_obj: Optional[py_date] = None
    if fecha_compra_lote_str:
        try: fecha_compra_obj = py_date.fromisoformat(fecha_compra_lote_str)
        except ValueError: errors.append({"loc": ["fecha_compra_lote"], "msg": "Formato de fecha de compra inválido. Use YYYY-MM-DD."})
    else: errors.append({"loc": ["fecha_compra_lote"], "msg": "Fecha de compra es obligatoria para editar."})


    fecha_vencimiento_obj: Optional[py_date] = None
    if fecha_vencimiento_lote_str:
        try: fecha_vencimiento_obj = py_date.fromisoformat(fecha_vencimiento_lote_str)
        except ValueError: errors.append({"loc": ["fecha_vencimiento_lote"], "msg": "Formato de fecha de vencimiento inválido. Use YYYY-MM-DD."})
    else: errors.append({"loc": ["fecha_vencimiento_lote"], "msg": "Fecha de vencimiento es obligatoria para editar."})

    if cantidad_cajas <=0: errors.append({"loc": ["cantidad_cajas"], "msg": "Cantidad de cajas debe ser positiva."})
    if unidades_por_caja_lote <=0: errors.append({"loc": ["unidades_por_caja_lote"], "msg": "Unidades por caja debe ser positivo."})

    if errors:
        return templates.TemplateResponse("form_lote.html", {
            "request": request, "form_title": f"Editar Lote #{lote_id} para: {medicamento.nombre}",
            "form_action": request.url_for("editar_lote_submit", lote_id=lote_id),
            "medicamento_info": medicamento, "lote": form_data_repop,
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=422)

    try:
        # Usamos LoteStockUpdate que tiene todos los campos opcionales.
        # La función crud.actualizar_lote_stock tomará solo los campos que se le pasen.
        lote_data_update = schemas.LoteStockUpdate(
            cantidad_cajas=cantidad_cajas, unidades_por_caja_lote=unidades_por_caja_lote,
            fecha_compra_lote=fecha_compra_obj,
            fecha_vencimiento_lote=fecha_vencimiento_obj,
            precio_compra_lote_por_caja=precio_compra_lote_por_caja
        )
    except ValidationError as e: # Otros errores de Pydantic
        return templates.TemplateResponse("form_lote.html", {
            "request": request, "form_title": f"Editar Lote #{lote_id} para: {medicamento.nombre}",
            "form_action": request.url_for("editar_lote_submit", lote_id=lote_id),
            "medicamento_info": medicamento, "lote": form_data_repop,
            "today_date_iso": py_date.today().isoformat(), "errors": e.errors()
        }, status_code=422)

    try:
        update_data_dict = lote_data_update.dict(exclude_unset=True)

        # Manejo especial para que un precio vacío signifique None
        if precio_compra_lote_por_caja is None and 'precio_compra_lote_por_caja' not in update_data_dict and lote_original.precio_compra_lote_por_caja is not None:
            update_data_dict['precio_compra_lote_por_caja'] = None

        if not update_data_dict: # Si no hay cambios efectivos
             return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=lote_original.medicamento_id), status_code=303)

        crud.actualizar_lote_stock(db, lote_id=lote_id, datos_actualizacion=update_data_dict)
        return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=lote_original.medicamento_id), status_code=303)
    except Exception as e:
        errors.append({"loc": ["general"], "msg": f"Error inesperado al actualizar el lote: {e}"})
        return templates.TemplateResponse("form_lote.html", {
            "request": request, "form_title": f"Editar Lote #{lote_id} para: {medicamento.nombre}",
            "form_action": request.url_for("editar_lote_submit", lote_id=lote_id),
            "medicamento_info": medicamento, "lote": form_data_repop,
            "today_date_iso": py_date.today().isoformat(), "errors": errors
        }, status_code=500)

@app.get("/lotes/{lote_id}/eliminar/", name="eliminar_lote_confirm_form")
async def eliminar_lote_confirm_form(request: Request, lote_id: int, db: Session = Depends(get_db_session_fastapi)):
    lote = crud.obtener_lote_stock(db, lote_id=lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado.")
    medicamento = crud.obtener_medicamento(db, medicamento_id=lote.medicamento_id)
    if not medicamento: # Improbable, pero por si acaso
         raise HTTPException(status_code=404, detail="Medicamento asociado al lote no encontrado.")

    return templates.TemplateResponse("confirmar_eliminacion_lote.html", {
        "request": request,
        "lote": lote,
        "medicamento_info": medicamento,
        "title": f"Confirmar Eliminación Lote #{lote.id}"
    })

@app.post("/lotes/{lote_id}/eliminar/", name="eliminar_lote_submit")
async def eliminar_lote_submit(request: Request, lote_id: int, db: Session = Depends(get_db_session_fastapi)):
    lote_a_eliminar = crud.obtener_lote_stock(db, lote_id=lote_id)
    if not lote_a_eliminar:
        raise HTTPException(status_code=404, detail="Lote no encontrado para eliminar.")

    medicamento_id_original = lote_a_eliminar.medicamento_id # Guardar antes de eliminar

    try:
        eliminado = crud.eliminar_lote_stock(db, lote_id=lote_id)
        if not eliminado:
             raise HTTPException(status_code=500, detail=f"No se pudo eliminar el lote ID {lote_id}.")

        return RedirectResponse(url=request.url_for("detalle_medicamento", medicamento_id=medicamento_id_original), status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el lote: {e}")


# Esta ruta debe ir DESPUÉS de las rutas CRUD de pedidos para evitar conflictos
@app.get("/pedidos/{pedido_id}/", name="detalle_pedido_ruta")
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

# --- Rutas para Reportes ---
@app.get("/reportes/costos-mensuales/", name="reporte_costos_mensuales")
async def reporte_costos_mensuales(
    request: Request,
    anio: Optional[int] = None, # Query param
    mes: Optional[int] = None,   # Query param
    db: Session = Depends(get_db_session_fastapi)
):
    meses_disponibles = crud.obtener_meses_con_pedidos(db) # Por defecto, para pedidos RECIBIDOS

    costo_calculado = None
    mes_seleccionado_info = None

    if anio is not None and mes is not None:
        # Validar que el mes y año sean razonables (básico)
        if not (1 <= mes <= 12 and 2000 <= anio <= py_date.today().year + 5):
            # Manejar error o simplemente no calcular
            pass # Opcionalmente, añadir un error a un contexto para la plantilla
        else:
            costo_calculado = crud.obtener_costos_pedidos_por_mes_anio(db, anio=anio, mes=mes)
            # Para mostrar el nombre del mes en la plantilla
            try:
                nombre_mes = py_date(anio, mes, 1).strftime('%B') # Nombre completo del mes
                mes_seleccionado_info = {"anio": anio, "mes_num": mes, "nombre_mes": nombre_mes.capitalize()}
            except ValueError: # Fecha inválida (ej. mes 13)
                 pass # ya validado arriba, pero por si acaso

    # Si no se selecciona anio/mes, podríamos mostrar todos los meses o un mensaje.
    # Por ahora, la plantilla manejará si costo_calculado es None.

    return templates.TemplateResponse("reporte_costos_mensuales.html", {
        "request": request,
        "meses_disponibles": meses_disponibles, # Para los selectores del formulario
        "anio_seleccionado": anio,
        "mes_seleccionado": mes,
        "mes_seleccionado_info": mes_seleccionado_info,
        "costo_calculado": costo_calculado,
        "title": "Reporte de Costos Mensuales de Pedidos"
    })

@app.get("/reportes/stock-por-vencimiento/", name="reporte_stock_vencimiento")
async def reporte_stock_por_vencimiento(request: Request, db: Session = Depends(get_db_session_fastapi)):
    lotes_por_vencimiento = crud.obtener_lotes_stock_ordenados_por_vencimiento(db)
    return templates.TemplateResponse("reporte_stock_vencimiento.html", {
        "request": request,
        "lotes": lotes_por_vencimiento,
        "title": "Reporte de Stock por Próximo Vencimiento"
    })

@app.get("/reportes/recetas-por-vencimiento/", name="reporte_recetas_vencimiento")
async def reporte_recetas_por_vencimiento(request: Request, db: Session = Depends(get_db_session_fastapi)):
    medicamentos_por_vencimiento_receta = crud.obtener_medicamentos_activos_por_vencimiento_receta(db)
    return templates.TemplateResponse("reporte_recetas_vencimiento.html", {
        "request": request,
        "medicamentos": medicamentos_por_vencimiento_receta,
        "today": py_date.today(), # Para calcular días restantes en la plantilla
        "title": "Reporte de Vencimiento de Recetas"
    })

# --- Ruta para Vista de Stock Global ---
@app.get("/stock/", name="vista_stock_global")
async def vista_stock_global(request: Request, db: Session = Depends(get_db_session_fastapi)):
    medicamentos = crud.obtener_medicamentos(db, limit=1000)
    stock_info_list = []
    valor_total_stock_general = 0.0

    for med in medicamentos:
        stock_total_unidades = crud.calcular_stock_total_unidades(db, med.id)
        valor_stock_medicamento = None
        precio_por_unidad_ref = None
        if med.precio_por_caja_referencia is not None and med.unidades_por_caja > 0:
            precio_por_unidad_ref = med.precio_por_caja_referencia / med.unidades_por_caja
            valor_stock_medicamento = stock_total_unidades * precio_por_unidad_ref
            if valor_stock_medicamento is not None: # Asegurarse de que valor_stock_medicamento no sea None antes de sumar
                 valor_total_stock_general += valor_stock_medicamento

        stock_info_list.append({
            "nombre": med.nombre,
            "marca": med.marca,
            "stock_total_unidades": stock_total_unidades,
            "valor_stock_medicamento": valor_stock_medicamento,
            "id": med.id,
            "esta_activo": med.esta_activo,
            "precio_por_unidad_referencia": precio_por_unidad_ref
        })

    return templates.TemplateResponse("vista_stock_global.html", {
        "request": request,
        "stock_info_list": stock_info_list,
        "valor_total_stock_general": valor_total_stock_general,
        "title": "Vista Global de Stock"
    })


if __name__ == "__main__":
    print("Para ejecutar esta aplicación web, use el comando:")
    print("uvicorn gestion_medicamentos.main_web:app --reload --port 8000")
    print(f"Asegúrese de estar en el directorio raíz del repositorio ('{os.path.dirname(current_dir)}') al ejecutar uvicorn.")

