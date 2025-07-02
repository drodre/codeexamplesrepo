from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# --- Medicamento Schemas ---
class MedicamentoBase(BaseModel):
    nombre: str
    marca: Optional[str] = None
    unidades_por_caja: int
    precio_por_caja_referencia: Optional[float] = None
    esta_activo: Optional[bool] = True
    vencimiento_receta: Optional[date] = None
    consumo_diario_unidades: Optional[float] = None

class MedicamentoCreate(MedicamentoBase):
    pass

class MedicamentoUpdate(MedicamentoBase):
    # Para actualizar, todos los campos son opcionales
    nombre: Optional[str] = None
    marca: Optional[str] = None
    unidades_por_caja: Optional[int] = None
    precio_por_caja_referencia: Optional[float] = None
    esta_activo: Optional[bool] = None # Permitir que se actualice, None significa no cambiar
    vencimiento_receta: Optional[date] = None # Permitir que se actualice o se borre (con None)
    consumo_diario_unidades: Optional[float] = None # Permitir actualizar o borrar (con None)

class MedicamentoSchema(MedicamentoBase):
    id: int
    esta_activo: bool # En el output, siempre será un booleano, no opcional
    vencimiento_receta: Optional[date] # Puede ser None en el output
    consumo_diario_unidades: Optional[float] # Puede ser None en el output

    class Config:
        orm_mode = True
        from_attributes = True # Para Pydantic V2, alias de orm_mode

# --- LoteStock Schemas ---
class LoteStockBase(BaseModel):
    # medicamento_id no se incluye aquí porque vendrá de la URL al crear/editar lotes para un medicamento específico.
    # Se añadirá en la lógica CRUD si es necesario pasarlo al modelo SQLAlchemy.
    cantidad_cajas: int
    unidades_por_caja_lote: int
    fecha_compra_lote: Optional[date] = None # El modelo SQL tiene default=func.current_date()
    fecha_vencimiento_lote: date # Esta sí es obligatoria al crear un lote
    precio_compra_lote_por_caja: Optional[float] = None

class LoteStockCreate(LoteStockBase):
    # Este schema se usará para validar los datos del formulario.
    # medicamento_id se pasará por separado a la función crud.
    pass

class LoteStockUpdate(BaseModel): # Usar BaseModel para flexibilidad total en actualización
    cantidad_cajas: Optional[int] = None
    unidades_por_caja_lote: Optional[int] = None
    fecha_compra_lote: Optional[date] = None
    fecha_vencimiento_lote: Optional[date] = None
    precio_compra_lote_por_caja: Optional[float] = None

class LoteStockSchema(LoteStockBase): # Hereda los campos de LoteStockBase
    id: int
    medicamento_id: int # Incluir para referencia al mostrar
    # medicamento: Optional[MedicamentoSchema] = None # Para mostrar info del medicamento al que pertenece, si se carga la relación

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
    pedido_id: int
    medicamento: MedicamentoSchema # Para mostrar info del medicamento en el detalle del pedido

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
