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
        orm_mode = True # Compatible con SQLAlchemy ORM (from_orm)

# --- LoteStock Schemas (Placeholder para futuro) ---
class LoteStockBase(BaseModel):
    medicamento_id: int
    cantidad_cajas: int
    unidades_por_caja_lote: int
    fecha_compra_lote: date
    fecha_vencimiento_lote: date
    precio_compra_lote_por_caja: Optional[float] = None

class LoteStockCreate(LoteStockBase):
    pass

class LoteStockSchema(LoteStockBase):
    id: int
    medicamento: MedicamentoSchema # Para mostrar info del medicamento al que pertenece

    class Config:
        orm_mode = True

# --- Pedido Schemas (Placeholder para futuro) ---
# class EstadoPedidoEnum(str, Enum): # Ya definido en models.py, ver cómo integrar o redefinir para Pydantic
#     PENDIENTE = "Pendiente"
#     RECIBIDO = "Recibido"
#     CANCELADO = "Cancelado"

class DetallePedidoBase(BaseModel):
    medicamento_id: int
    cantidad_cajas_pedidas: int
    precio_unitario_compra_caja: Optional[float] = None

class DetallePedidoCreate(DetallePedidoBase):
    pass

class DetallePedidoSchema(DetallePedidoBase):
    id: int
    # medicamento: MedicamentoSchema # Para mostrar info del medicamento

    class Config:
        orm_mode = True


class PedidoBase(BaseModel):
    fecha_pedido: Optional[date] = None
    proveedor: Optional[str] = None
    # estado: EstadoPedidoEnum # Ver models.EstadoPedido

class PedidoCreate(PedidoBase):
    # detalles: Optional[List[DetallePedidoCreate]] = [] # Para crear con detalles
    pass

class PedidoSchema(PedidoBase):
    id: int
    # estado: str # Para mostrar el valor del enum
    # detalles: List[DetallePedidoSchema] = []
    # costo_total_pedido: Optional[float] = None # Se calculará

    class Config:
        orm_mode = True


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
