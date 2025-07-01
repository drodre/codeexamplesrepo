from sqlalchemy import create_engine, Column, Integer, String, Date, Float, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func # Para valores por defecto como now()
import enum

Base = declarative_base()

class EstadoPedido(enum.Enum):
    PENDIENTE = "Pendiente"
    RECIBIDO = "Recibido"
    CANCELADO = "Cancelado"

class Medicamento(Base):
    __tablename__ = "medicamentos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String, nullable=False, index=True)
    marca = Column(String, nullable=True)
    unidades_por_caja = Column(Integer, nullable=False)
    # El stock_total_unidades se calculará dinámicamente a partir de LotesStock
    # duracion_por_caja_dias = Column(Integer, nullable=True) # Considerar si es mejor calcularlo o si es fijo
    # fecha_ultima_compra se puede obtener del lote más reciente
    # fecha_vencimiento_proxima se puede obtener del lote con vencimiento más cercano
    precio_por_caja_referencia = Column(Float, nullable=True) # Precio de referencia o último conocido
    esta_activo = Column(Boolean, default=True, nullable=False, server_default='t') # Asumiendo True para la mayoría de BDs

    lotes = relationship("LoteStock", back_populates="medicamento", cascade="all, delete-orphan")
    detalles_pedido = relationship("DetallePedido", back_populates="medicamento")

    def __repr__(self):
        return f"<Medicamento(id={self.id}, nombre='{self.nombre}', marca='{self.marca}')>"

class LoteStock(Base):
    __tablename__ = "lotes_stock"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.id"), nullable=False)
    cantidad_cajas = Column(Integer, nullable=False)
    unidades_por_caja_lote = Column(Integer, nullable=False) # Unidades por caja para este lote específico
    fecha_compra_lote = Column(Date, nullable=False, default=func.current_date())
    fecha_vencimiento_lote = Column(Date, nullable=False)
    precio_compra_lote_por_caja = Column(Float, nullable=True)

    medicamento = relationship("Medicamento", back_populates="lotes")

    @property
    def unidades_totales_lote(self):
        return self.cantidad_cajas * self.unidades_por_caja_lote

    def __repr__(self):
        return f"<LoteStock(id={self.id}, med_id={self.medicamento_id}, cajas={self.cantidad_cajas}, venc='{self.fecha_vencimiento_lote}')>"

class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha_pedido = Column(Date, nullable=False, default=func.current_date())
    proveedor = Column(String, nullable=True)
    # costo_total_pedido se calculará a partir de los DetallesPedido
    estado = Column(SQLAlchemyEnum(EstadoPedido), nullable=False, default=EstadoPedido.PENDIENTE)

    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pedido(id={self.id}, fecha='{self.fecha_pedido}', estado='{self.estado.value}')>"

class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.id"), nullable=False)
    cantidad_cajas_pedidas = Column(Integer, nullable=False)
    precio_unitario_compra_caja = Column(Float, nullable=True) # Precio por caja en este pedido

    pedido = relationship("Pedido", back_populates="detalles")
    medicamento = relationship("Medicamento", back_populates="detalles_pedido")

    @property
    def subtotal_detalle(self):
        if self.precio_unitario_compra_caja is not None:
            return self.cantidad_cajas_pedidas * self.precio_unitario_compra_caja
        return 0

    def __repr__(self):
        return f"<DetallePedido(id={self.id}, pedido_id={self.pedido_id}, med_id={self.medicamento_id}, cajas={self.cantidad_cajas_pedidas})>"

# Ejemplo de cómo se podría calcular el stock total o la fecha de vencimiento próxima en la lógica de la aplicación:
# (Esto no va en models.py, sino en la capa de servicio/lógica)
#
# def get_stock_total_unidades(session, medicamento_id: int) -> int:
#     medicamento = session.query(Medicamento).filter(Medicamento.id == medicamento_id).first()
#     if not medicamento:
#         return 0
#     total_unidades = 0
#     for lote in medicamento.lotes:
#         # Aquí se podría añadir una condición para contar solo lotes no vencidos si es necesario
#         if lote.fecha_vencimiento_lote >= date.today(): # Asumiendo que date.today() está disponible
#             total_unidades += lote.unidades_totales_lote
#     return total_unidades
#
# def get_fecha_vencimiento_proxima(session, medicamento_id: int) -> Date | None:
#     medicamento = session.query(Medicamento).filter(Medicamento.id == medicamento_id).first()
#     if not medicamento or not medicamento.lotes:
#         return None
#
#     fecha_proxima = None
#     today = date.today() # Asumiendo que date.today() está disponible
#
#     for lote in medicamento.lotes:
#         if lote.fecha_vencimiento_lote >= today:
#             if fecha_proxima is None or lote.fecha_vencimiento_lote < fecha_proxima:
#                 fecha_proxima = lote.fecha_vencimiento_lote
#     return fecha_proxima
#
# def get_costo_total_pedido(pedido: Pedido) -> float:
#     total = 0
#     for detalle in pedido.detalles:
#         total += detalle.subtotal_detalle
#     return total

# Nota: He comentado algunas propiedades calculadas que estaban directamente en la tabla Medicamentos
# porque es mejor práctica calcularlas dinámicamente desde los LotesStock o DetallesPedido
# para asegurar la consistencia de los datos. Por ejemplo:
# - `stock_total_unidades` en `Medicamentos` se calculará sumando `unidades_totales_lote` de los `LotesStock` activos.
# - `fecha_vencimiento_proxima` en `Medicamentos` se determinará buscando la `fecha_vencimiento_lote` más temprana entre los `LotesStock` activos.
# - `costo_total_pedido` en `Pedidos` se calculará sumando `subtotal_detalle` de sus `DetallesPedido`.
# He dejado `precio_por_caja_referencia` en `Medicamentos` como un precio de referencia general o el último conocido,
# mientras que `precio_compra_lote_por_caja` en `LoteStock` y `precio_unitario_compra_caja` en `DetallePedido`
# registrarán los precios exactos al momento de la compra o pedido.
#
# También añadí un Enum para el estado del pedido.
# Se ha usado `default=func.current_date()` para las fechas de compra y pedido.
# Se ha añadido `index=True` a campos que probablemente se usarán en búsquedas frecuentes.
# `cascade="all, delete-orphan"` se ha añadido a relaciones para que al borrar un padre, se borren los hijos.
# Por ejemplo, si borras un Medicamento, se borrarán sus LotesStock asociados. Si borras un Pedido, sus Detalles.
# Se utiliza `SQLAlchemyEnum` para el campo estado en Pedido.
# He renombrado `precio_por_caja` en `Medicamentos` a `precio_por_caja_referencia` para evitar confusión.
# He añadido `unidades_por_caja_lote` a `LoteStock` para permitir flexibilidad si se compran diferentes formatos del mismo medicamento.
# He añadido `autoincrement=True` explícitamente a las claves primarias por claridad, aunque suele ser el comportamiento por defecto para `Integer, primary_key=True`.
