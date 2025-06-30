# Este archivo contendrá las funciones para Crear, Leer, Actualizar y Eliminar (CRUD)
# datos de la base de datos.

# Importaciones necesarias al inicio del archivo
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, and_
from . import models # models.py en el mismo directorio
from datetime import date as py_date, timedelta # Renombrado para evitar conflicto y añadido timedelta
from typing import List, Optional, Type, Dict, Any # Para type hints

# Más adelante añadiremos aquí las funciones CRUD específicas.

# --- Funciones CRUD para Medicamento ---

def crear_medicamento(db: Session, nombre: str, marca: Optional[str], unidades_por_caja: int, precio_por_caja_referencia: Optional[float] = None) -> models.Medicamento:
    """
    Crea un nuevo registro de medicamento en la base de datos.
    """
    db_medicamento = models.Medicamento(
        nombre=nombre,
        marca=marca,
        unidades_por_caja=unidades_por_caja,
        precio_por_caja_referencia=precio_por_caja_referencia # Nombre de parámetro corregido
    )
    db.add(db_medicamento)
    db.commit()
    db.refresh(db_medicamento)
    return db_medicamento

def obtener_medicamento(db: Session, medicamento_id: int) -> Optional[models.Medicamento]:
    """
    Obtiene un medicamento por su ID.
    """
    return db.query(models.Medicamento).filter(models.Medicamento.id == medicamento_id).first()

def obtener_medicamento_por_nombre(db: Session, nombre: str) -> Optional[models.Medicamento]:
    """
    Obtiene un medicamento por su nombre.
    """
    return db.query(models.Medicamento).filter(func.lower(models.Medicamento.nombre) == func.lower(nombre)).first()

def obtener_medicamentos(db: Session, skip: int = 0, limit: int = 100) -> List[models.Medicamento]:
    """
    Obtiene una lista de medicamentos, con paginación opcional.
    """
    return db.query(models.Medicamento).offset(skip).limit(limit).all()

def actualizar_medicamento(db: Session, medicamento_id: int, datos_actualizacion: dict) -> Optional[models.Medicamento]:
    """
    Actualiza un medicamento existente.
    `datos_actualizacion` es un diccionario con los campos a actualizar.
    Ej: {'nombre': 'Nuevo Nombre', 'marca': 'Nueva Marca'}
    """
    db_medicamento = obtener_medicamento(db, medicamento_id)
    if db_medicamento:
        for key, value in datos_actualizacion.items():
            if hasattr(db_medicamento, key):
                setattr(db_medicamento, key, value)
            else:
                # Opcional: lanzar un error si la clave no es válida
                print(f"Advertencia: El campo '{key}' no existe en el modelo Medicamento y será ignorado.")
        db.commit()
        db.refresh(db_medicamento)
    return db_medicamento

def eliminar_medicamento(db: Session, medicamento_id: int) -> bool:
    """
    Elimina un medicamento por su ID.
    Devuelve True si la eliminación fue exitosa, False en caso contrario.
    Nota: Esto también eliminará los LotesStock y DetallesPedido asociados
    debido a la configuración de `cascade="all, delete-orphan"` en los modelos.
    """
    db_medicamento = obtener_medicamento(db, medicamento_id)
    if db_medicamento:
        db.delete(db_medicamento)
        db.commit()
        return True
    return False

# --- Funciones de Utilidad/Calculadas para Medicamento ---

def calcular_stock_total_unidades(db: Session, medicamento_id: int) -> int:
    """
    Calcula el stock total de unidades para un medicamento, sumando las unidades
    de todos sus lotes activos (no vencidos).
    """
    medicamento = obtener_medicamento(db, medicamento_id)
    if not medicamento:
        return 0 # O podrías lanzar un error: raise ValueError(f"Medicamento con ID {medicamento_id} no encontrado")

    total_unidades = 0
    lotes_activos = obtener_lotes_por_medicamento(db, medicamento_id, solo_activos=True)

    for lote in lotes_activos:
        total_unidades += lote.unidades_totales_lote # Usando la property del modelo LoteStock
    return total_unidades

def calcular_fecha_vencimiento_proxima(db: Session, medicamento_id: int) -> Optional[py_date]:
    """
    Calcula la fecha de vencimiento más próxima entre los lotes activos
    de un medicamento.
    """
    lotes_activos = obtener_lotes_por_medicamento(db, medicamento_id, solo_activos=True)

    if not lotes_activos:
        return None

    # Los lotes ya vienen ordenados por fecha_vencimiento_lote de forma ascendente
    # gracias a la función obtener_lotes_por_medicamento
    return lotes_activos[0].fecha_vencimiento_lote

# --- Funciones CRUD para Pedido ---

def crear_pedido(db: Session, fecha_pedido: Optional[py_date] = None, proveedor: Optional[str] = None,
                 estado: models.EstadoPedido = models.EstadoPedido.PENDIENTE) -> models.Pedido:
    """
    Crea un nuevo pedido.
    Si fecha_pedido no se proporciona, se usará la fecha actual por defecto del modelo.
    """
    db_pedido = models.Pedido(
        proveedor=proveedor,
        estado=estado
    )
    if fecha_pedido: # Solo asignar si se proporciona, sino usa el default del modelo
        db_pedido.fecha_pedido = fecha_pedido

    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido

def obtener_pedido(db: Session, pedido_id: int) -> Optional[models.Pedido]:
    """
    Obtiene un pedido por su ID, incluyendo sus detalles.
    """
    return db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()
    # Los detalles se cargarán automáticamente si se accede a pedido.detalles
    # o se puede usar options(selectinload(models.Pedido.detalles)) para carga eager.

def obtener_pedidos(db: Session, skip: int = 0, limit: int = 100) -> List[models.Pedido]:
    """
    Obtiene una lista de pedidos, con paginación opcional.
    """
    return db.query(models.Pedido).order_by(models.Pedido.fecha_pedido.desc()).offset(skip).limit(limit).all()

def actualizar_pedido(db: Session, pedido_id: int, datos_actualizacion: dict) -> Optional[models.Pedido]:
    """
    Actualiza un pedido existente.
    `datos_actualizacion` es un diccionario con los campos a actualizar.
    Ej: {'proveedor': 'Farmacia Central', 'estado': models.EstadoPedido.RECIBIDO}
    """
    db_pedido = obtener_pedido(db, pedido_id)
    if db_pedido:
        for key, value in datos_actualizacion.items():
            if hasattr(db_pedido, key):
                # Especial manejo para el Enum si se pasa como string
                if key == "estado" and isinstance(value, str):
                    try:
                        value = models.EstadoPedido[value.upper()]
                    except KeyError:
                        print(f"Advertencia: Valor de estado '{value}' no válido. Se ignora la actualización de estado.")
                        continue
                setattr(db_pedido, key, value)
            else:
                print(f"Advertencia: El campo '{key}' no existe en el modelo Pedido y será ignorado.")
        db.commit()
        db.refresh(db_pedido)
    return db_pedido

def eliminar_pedido(db: Session, pedido_id: int) -> bool:
    """
    Elimina un pedido por su ID.
    Esto también eliminará los DetallesPedido asociados debido a `cascade="all, delete-orphan"`.
    Devuelve True si la eliminación fue exitosa, False en caso contrario.
    """
    db_pedido = obtener_pedido(db, pedido_id)
    if db_pedido:
        db.delete(db_pedido)
        db.commit()
        return True
    return False

# --- Funciones de Utilidad/Calculadas para Pedido ---

def calcular_costo_total_pedido(db: Session, pedido_id: int) -> float:
    """
    Calcula el costo total de un pedido sumando los subtotales de sus detalles.
    """
    pedido = obtener_pedido(db, pedido_id) # Esta función ya podría cargar los detalles si se configura con eager loading
                                         # o podemos cargarlos explícitamente si es necesario.
    if not pedido:
        # O podrías lanzar un error: raise ValueError(f"Pedido con ID {pedido_id} no encontrado")
        return 0.0

    # Si los detalles no se cargan automáticamente (lazy loading es el default):
    # detalles = obtener_detalles_por_pedido(db, pedido_id)
    # Pero como Pedido tiene la relación 'detalles', SQLAlchemy los cargará al acceder.

    costo_total = 0.0
    if pedido and pedido.detalles: # Asegurarse de que pedido y pedido.detalles no son None
        for detalle in pedido.detalles:
            costo_total += detalle.subtotal_detalle
    return costo_total

# --- Funciones para Reportes ---

def obtener_costos_pedidos_por_mes_anio(db: Session, anio: int, mes: int, estado_filtro: Optional[models.EstadoPedido] = models.EstadoPedido.RECIBIDO) -> float:
    """
    Calcula el costo total de los pedidos para un mes y año específicos,
    opcionalmente filtrando por estado del pedido (por defecto 'RECIBIDO').
    """
    query = db.query(models.Pedido).filter(
        func.extract('year', models.Pedido.fecha_pedido) == anio,
        func.extract('month', models.Pedido.fecha_pedido) == mes
    )
    if estado_filtro:
        query = query.filter(models.Pedido.estado == estado_filtro)

    pedidos_del_mes = query.all()

    costo_total_mes = 0.0
    for pedido in pedidos_del_mes:
        costo_total_mes += calcular_costo_total_pedido(db, pedido.id) # Reutilizamos la función existente

    return costo_total_mes

def obtener_meses_con_pedidos(db: Session, estado_filtro: Optional[models.EstadoPedido] = models.EstadoPedido.RECIBIDO) -> List[dict]:
    """
    Obtiene una lista de diccionarios {'anio': anio, 'mes': mes} para los cuales
    existen pedidos, opcionalmente filtrando por estado (por defecto 'RECIBIDO').
    Los resultados se devuelven ordenados por año y mes descendente.
    """
    query = db.query(
        func.extract('year', models.Pedido.fecha_pedido).label('anio'),
        func.extract('month', models.Pedido.fecha_pedido).label('mes')
    ).distinct()

    if estado_filtro:
        query = query.filter(models.Pedido.estado == estado_filtro)

    # Ordenar por año descendente, luego por mes descendente
    resultados = query.order_by(
        func.extract('year', models.Pedido.fecha_pedido).desc(),
        func.extract('month', models.Pedido.fecha_pedido).desc()
    ).all()

    # Convertir los resultados (Row objects) a una lista de diccionarios
    meses_disponibles = []
    for row in resultados:
        meses_disponibles.append({'anio': int(row.anio), 'mes': int(row.mes)})

    return meses_disponibles


# --- Funciones CRUD para DetallePedido ---

def agregar_detalle_pedido(db: Session, pedido_id: int, medicamento_id: int, cantidad_cajas_pedidas: int,
                           precio_unitario_compra_caja: Optional[float] = None) -> models.DetallePedido:
    """
    Agrega un detalle (ítem) a un pedido existente.
    """
    # Verificar que el pedido y el medicamento existan
    pedido = obtener_pedido(db, pedido_id)
    if not pedido:
        raise ValueError(f"No se encontró el pedido con ID {pedido_id}")
    medicamento = obtener_medicamento(db, medicamento_id)
    if not medicamento:
        raise ValueError(f"No se encontró el medicamento con ID {medicamento_id}")

    db_detalle_pedido = models.DetallePedido(
        pedido_id=pedido_id,
        medicamento_id=medicamento_id,
        cantidad_cajas_pedidas=cantidad_cajas_pedidas,
        precio_unitario_compra_caja=precio_unitario_compra_caja
    )
    db.add(db_detalle_pedido)
    db.commit()
    db.refresh(db_detalle_pedido)
    return db_detalle_pedido

def obtener_detalle_pedido(db: Session, detalle_id: int) -> Optional[models.DetallePedido]:
    """
    Obtiene un detalle de pedido por su ID.
    """
    return db.query(models.DetallePedido).filter(models.DetallePedido.id == detalle_id).first()

def obtener_detalles_por_pedido(db: Session, pedido_id: int) -> List[models.DetallePedido]:
    """
    Obtiene todos los detalles para un pedido específico.
    """
    return db.query(models.DetallePedido).filter(models.DetallePedido.pedido_id == pedido_id).all()

def actualizar_detalle_pedido(db: Session, detalle_id: int, datos_actualizacion: dict) -> Optional[models.DetallePedido]:
    """
    Actualiza un detalle de pedido existente.
    `datos_actualizacion` es un diccionario con los campos a actualizar.
    """
    db_detalle = obtener_detalle_pedido(db, detalle_id)
    if db_detalle:
        for key, value in datos_actualizacion.items():
            if hasattr(db_detalle, key):
                setattr(db_detalle, key, value)
            else:
                print(f"Advertencia: El campo '{key}' no existe en el modelo DetallePedido y será ignorado.")
        db.commit()
        db.refresh(db_detalle)
    return db_detalle

def eliminar_detalle_pedido(db: Session, detalle_id: int) -> bool:
    """
    Elimina un detalle de pedido por su ID.
    Devuelve True si la eliminación fue exitosa, False en caso contrario.
    """
    db_detalle = obtener_detalle_pedido(db, detalle_id)
    if db_detalle:
        db.delete(db_detalle)
        db.commit()
        return True
    return False

# --- Funciones CRUD para LoteStock ---

def agregar_lote_stock(db: Session, medicamento_id: int, cantidad_cajas: int, unidades_por_caja_lote: int,
                       fecha_vencimiento_lote: py_date, fecha_compra_lote: Optional[py_date] = None,
                       precio_compra_lote_por_caja: Optional[float] = None) -> models.LoteStock:
    """
    Agrega un nuevo lote de stock para un medicamento existente.
    Si fecha_compra_lote no se proporciona, se usará la fecha actual por defecto del modelo.
    """
    # Verificar que el medicamento exista
    medicamento = obtener_medicamento(db, medicamento_id)
    if not medicamento:
        raise ValueError(f"No se encontró el medicamento con ID {medicamento_id}")

    db_lote = models.LoteStock(
        medicamento_id=medicamento_id,
        cantidad_cajas=cantidad_cajas,
        unidades_por_caja_lote=unidades_por_caja_lote,
        fecha_vencimiento_lote=fecha_vencimiento_lote,
        precio_compra_lote_por_caja=precio_compra_lote_por_caja
    )
    if fecha_compra_lote: # Solo asignar si se proporciona, sino usa el default del modelo
        db_lote.fecha_compra_lote = fecha_compra_lote

    db.add(db_lote)
    db.commit()
    db.refresh(db_lote)
    return db_lote

def obtener_lote_stock(db: Session, lote_id: int) -> Optional[models.LoteStock]:
    """
    Obtiene un lote de stock por su ID.
    """
    return db.query(models.LoteStock).filter(models.LoteStock.id == lote_id).first()

def obtener_lotes_por_medicamento(db: Session, medicamento_id: int, solo_activos: bool = False) -> List[models.LoteStock]:
    """
    Obtiene todos los lotes de stock para un medicamento específico.
    Si solo_activos es True, filtra los lotes no vencidos.
    """
    query = db.query(models.LoteStock).filter(models.LoteStock.medicamento_id == medicamento_id)
    if solo_activos:
        query = query.filter(models.LoteStock.fecha_vencimiento_lote >= py_date.today())
    return query.order_by(models.LoteStock.fecha_vencimiento_lote).all() # Ordenar por fecha de vencimiento


# --- Funciones para el Dashboard ---

def contar_total_medicamentos(db: Session) -> int:
    """Cuenta el número total de medicamentos distintos registrados."""
    return db.query(func.count(models.Medicamento.id.distinct())).scalar()

def contar_medicamentos_proximos_a_vencer(db: Session, dias_limite: int) -> int:
    """
    Cuenta el número de medicamentos distintos que tienen al menos un lote activo
    cuya fecha de vencimiento está dentro de los próximos `dias_limite`.
    Un lote está activo si su fecha de vencimiento es hoy o en el futuro.
    """
    fecha_referencia = py_date.today() + timedelta(days=dias_limite)
    hoy = py_date.today()

    # Subconsulta para obtener los medicamento_id de los lotes que cumplen la condición
    subquery = db.query(models.LoteStock.medicamento_id)\
        .filter(models.LoteStock.fecha_vencimiento_lote >= hoy)\
        .filter(models.LoteStock.fecha_vencimiento_lote <= fecha_referencia)\
        .distinct()\
        .subquery()

    # Contar cuántos medicamentos distintos tienen lotes en esa condición
    count = db.query(func.count(subquery.c.medicamento_id)).scalar()
    return count

def contar_lotes_vencidos_no_eliminados(db: Session) -> int:
    """
    Cuenta el número total de lotes individuales que ya han vencido.
    Asume que "no eliminados" significa que simplemente existen en la tabla LoteStock.
    """
    hoy = py_date.today()
    return db.query(models.LoteStock)\
        .filter(models.LoteStock.fecha_vencimiento_lote < hoy)\
        .count()

def contar_medicamentos_stock_bajo(db: Session, umbral_unidades: int) -> int:
    """
    Cuenta el número de medicamentos distintos cuyo stock total de unidades activas
    es menor o igual al `umbral_unidades`.
    El stock activo se calcula sumando unidades de lotes no vencidos.
    """
    hoy = py_date.today()

    # Subconsulta para calcular el stock total activo por medicamento
    # (cantidad_cajas * unidades_por_caja_lote)
    subquery_stock_activo = db.query(
            models.LoteStock.medicamento_id,
            func.sum(models.LoteStock.cantidad_cajas * models.LoteStock.unidades_por_caja_lote).label("stock_activo_total")
        )\
        .filter(models.LoteStock.fecha_vencimiento_lote >= hoy)\
        .group_by(models.LoteStock.medicamento_id)\
        .subquery()

    # Contar medicamentos cuyo stock (considerando 0 si no hay lotes activos o el medicamento no tiene lotes)
    # es <= umbral. Usamos un LEFT JOIN para incluir medicamentos sin lotes activos (stock 0).
    # COALESCE se usa para tratar los NULL (medicamentos sin lotes activos) como 0.
    count = db.query(models.Medicamento.id)\
        .outerjoin(subquery_stock_activo, models.Medicamento.id == subquery_stock_activo.c.medicamento_id)\
        .filter(func.coalesce(subquery_stock_activo.c.stock_activo_total, 0) <= umbral_unidades)\
        .count()

    return count

# --- Fin Funciones para el Dashboard ---


def actualizar_lote_stock(db: Session, lote_id: int, datos_actualizacion: dict) -> Optional[models.LoteStock]:
    """
    Actualiza un lote de stock existente.
    `datos_actualizacion` es un diccionario con los campos a actualizar.
    """
    db_lote = obtener_lote_stock(db, lote_id)
    if db_lote:
        for key, value in datos_actualizacion.items():
            if hasattr(db_lote, key):
                setattr(db_lote, key, value)
            else:
                print(f"Advertencia: El campo '{key}' no existe en el modelo LoteStock y será ignorado.")
        db.commit()
        db.refresh(db_lote)
    return db_lote

def eliminar_lote_stock(db: Session, lote_id: int) -> bool:
    """
    Elimina un lote de stock por su ID.
    Devuelve True si la eliminación fue exitosa, False en caso contrario.
    """
    db_lote = obtener_lote_stock(db, lote_id)
    if db_lote:
        db.delete(db_lote)
        db.commit()
        return True
    return False
