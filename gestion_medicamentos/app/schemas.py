from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# --- Medicamento Schemas ---
class MedicamentoBase(BaseModel):
    nombre: str
    marca: Optional[str] = None
    unidades_por_caja: int
    precio_por_caja_referencia: Optional[float] = None

class MedicamentoCreate(MedicamentoBase):
    pass

class MedicamentoUpdate(MedicamentoBase):
    # Para actualizar, todos los campos son opcionales
    nombre: Optional[str] = None
    marca: Optional[str] = None
    unidades_por_caja: Optional[int] = None
    precio_por_caja_referencia: Optional[float] = None

class MedicamentoSchema(MedicamentoBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True # Para Pydantic V2, alias de orm_mode

# --- LoteStock Schemas ---
class LoteStockBase(BaseModel):
    medicamento_id: int
    cantidad_cajas: int
    unidades_por_caja_lote: int
    fecha_compra_lote: date # Hacerla opcional si el modelo tiene default? Modelo tiene default.
    fecha_vencimiento_lote: date
    precio_compra_lote_por_caja: Optional[float] = None

class LoteStockCreate(LoteStockBase):
    fecha_compra_lote: Optional[date] = None # Coincide con el default del modelo SQL

class LoteStockSchema(LoteStockBase):
    id: int
    # medicamento: MedicamentoSchema # Descomentar si es necesario en respuestas

    class Config:
        orm_mode = True
        from_attributes = True

# --- DetallePedido Schemas ---
class DetallePedidoBase(BaseModel):
    medicamento_id: int
    cantidad_cajas_pedidas: int
    precio_unitario_compra_caja: Optional[float] = None

class DetallePedidoCreate(DetallePedidoBase):
    pass

class DetallePedidoSchema(DetallePedidoBase):
    id: int
    pedido_id: int # Añadido para referencia
    # medicamento: MedicamentoSchema # Descomentar si es necesario en respuestas

    class Config:
        orm_mode = True
        from_attributes = True

# --- Pedido Schemas ---
# Importar el Enum del modelo para usarlo en Pydantic
from .models import EstadoPedido as EstadoPedidoEnum

class PedidoBase(BaseModel):
    fecha_pedido: Optional[date] = None # El modelo SQL tiene default, así que puede ser opcional aquí
    proveedor: Optional[str] = None
    estado: EstadoPedidoEnum = EstadoPedidoEnum.PENDIENTE # Usar el Enum del modelo

class PedidoCreate(PedidoBase):
    # No se incluyen detalles aquí por ahora, se añadirán por separado.
    pass

class PedidoUpdate(PedidoBase):
    # Para actualizar, todos los campos son opcionales
    fecha_pedido: Optional[date] = None
    proveedor: Optional[str] = None
    estado: Optional[EstadoPedidoEnum] = None

class PedidoSchema(PedidoBase):
    id: int
    detalles: List[DetallePedidoSchema] = [] # Para mostrar los ítems del pedido
    # costo_total_pedido: float # Se calculará en la vista/ruta, no es parte del modelo directo

    class Config:
        orm_mode = True
        from_attributes = True


# Actualizar MedicamentoSchema para incluir lotes (ejemplo de cómo se podría hacer)
# class MedicamentoWithLotesSchema(MedicamentoSchema):
#     lotes: List[LoteStockSchema] = []

# Nota: Por ahora, los schemas de LoteStock, Pedido y DetallePedido son placeholders y
# se desarrollarán más cuando implementemos su CRUD web.
# El schema `MedicamentoUpdate` permite que todos los campos sean opcionales,
# lo que es útil para actualizaciones parciales (PATCH) o formularios donde
# no todos los campos se envían si no cambian.
# `orm_mode = True` (o `from_attributes = True` en Pydantic V2) permite que los modelos Pydantic
# se creen a partir de objetos ORM de SQLAlchemy.
# FastAPI usará estos schemas para validación de datos de request y para formatear responses.
