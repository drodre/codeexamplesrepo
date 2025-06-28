# Archivo principal para la Interfaz de Línea de Comandos (CLI)
# de la aplicación de Gestión de Medicamentos.

import sys
import os # Importar os
from datetime import datetime, date
from typing import Optional # Asegurar que Optional esté importado

# Necesitaremos acceder a los módulos de la app
# Esto asume que ejecutaremos main_cli.py desde el directorio raíz del repositorio,
# o que gestion_medicamentos está en el PYTHONPATH.
# Para simplificar, si ejecutamos desde gestion_medicamentos/, ajustamos path.
try:
    from app import crud, models, database
except ImportError:
    # Si estamos ejecutando directamente gestion_medicamentos/main_cli.py
    # necesitamos añadir el directorio padre (gestion_medicamentos) al path
    # para que encuentre el paquete 'app'.
    import os
    # Obtener el directorio del script actual (gestion_medicamentos/main_cli.py)
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # Añadir el directorio padre (gestion_medicamentos) a sys.path
    # Esto hace que 'app' sea importable como un paquete.
    # sys.path.insert(0, os.path.dirname(current_script_dir)) # Esto añadiría el directorio raíz del repo
    sys.path.insert(0, current_script_dir) # Esto añade gestion_medicamentos al path

    from app import crud, models, database


def obtener_sesion_db():
    """
    Genera una sesión de base de datos.
    """
    db_gen = database.get_db()
    db = next(db_gen)
    try:
        yield db
    finally:
        next(db_gen, None) # Asegura que la sesión se cierre correctamente

def main():
    # Crear tablas si no existen (esto es seguro llamarlo múltiples veces)
    # Aunque es mejor tener un script de inicialización separado, para una CLI simple está bien aquí.
    # database.create_db_and_tables() # Movido al bloque if __name__ == "__main__":
    print("\nBienvenido al Gestor de Medicamentos Caseros")

    while True:
        print("\n╔══════════════════════════════════╗")
        print("║        MENÚ PRINCIPAL            ║")
        print("╠══════════════════════════════════╣")
        print("1. Gestionar Medicamentos")
        print("2. Gestionar Stock (Lotes)")
        print("║ 1. Gestionar Medicamentos        ║")
        print("║ 2. Gestionar Stock (Lotes)       ║")
        print("║ 3. Gestionar Pedidos             ║")
        print("║ 4. Salir                         ║")
        print("╚══════════════════════════════════╝")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == '1':
            menu_medicamentos()
        elif opcion == '2':
            menu_stock()
        elif opcion == '3':
            menu_pedidos()
        elif opcion == '4':
            print("Saliendo del gestor de medicamentos. ¡Hasta pronto!")
            break
        else:
            print("Opción no válida. Por favor, intente de nuevo.")

# --- Funciones de Menú ---
def _imprimir_subtitulo(titulo: str):
    print(f"\n--- {titulo} ---")

def menu_medicamentos():
    while True:
        _imprimir_subtitulo("Gestionar Medicamentos")
        print("1. Añadir nuevo medicamento")
        print("2. Ver detalle de un medicamento")
        print("3. Listar todos los medicamentos")
        print("4. Actualizar medicamento")
        print("5. Eliminar medicamento")
        print("6. Ver stock total y vencimiento próximo de un medicamento")
        print("0. Volver al menú principal")

        opcion_med = input("Seleccione una opción: ").strip()

        with obtener_sesion_db() as db:
            if opcion_med == '1':
                # Añadir nuevo medicamento
                nombre = input("Nombre del medicamento: ").strip()
                if not nombre:
                    print("El nombre no puede estar vacío.")
                    continue
                marca = input("Marca (opcional): ").strip()
                while True:
                    try:
                        unidades_str = input("Unidades por caja: ").strip()
                        if not unidades_str:
                            print("Las unidades por caja no pueden estar vacías.")
                            continue
                        unidades = int(unidades_str)
                        if unidades <= 0:
                            print("Las unidades por caja deben ser un número positivo.")
                            continue
                        break
                    except ValueError:
                        print("Entrada inválida. Por favor, ingrese un número entero para las unidades.")

                precio_str = input("Precio de referencia por caja (opcional, ej. 10.50): ").strip()
                precio = None
                if precio_str:
                    try:
                        precio = float(precio_str)
                    except ValueError:
                        print("Precio no válido, se guardará sin precio de referencia.")

                try:
                    medicamento_existente = crud.obtener_medicamento_por_nombre(db, nombre=nombre)
                    if medicamento_existente:
                        print(f"Error: Ya existe un medicamento con el nombre '{nombre}'.")
                    else:
                        medicamento = crud.crear_medicamento(db, nombre=nombre, marca=marca if marca else None,
                                                             unidades_por_caja=unidades, precio_referencia=precio)
                        print(f"Medicamento '{medicamento.nombre}' añadido con ID: {medicamento.id}")
                except Exception as e:
                    print(f"Error al crear el medicamento: {e}")

            elif opcion_med == '2':
                # Ver detalle de un medicamento
                try:
                    med_id_str = input("ID del medicamento a ver: ").strip()
                    if not med_id_str:
                        print("El ID no puede estar vacío.")
                        continue
                    med_id = int(med_id_str)
                    medicamento = crud.obtener_medicamento(db, med_id)
                    if medicamento:
                        print(f"\n--- Detalle del Medicamento ID: {medicamento.id} ---")
                        print(f"Nombre: {medicamento.nombre}")
                        print(f"Marca: {medicamento.marca if medicamento.marca else 'N/A'}")
                        print(f"Unidades por caja: {medicamento.unidades_por_caja}")
                        print(f"Precio de referencia: {medicamento.precio_por_caja_referencia if medicamento.precio_por_caja_referencia is not None else 'N/A'}")
                        # Stock y vencimiento se ven en opción 6 o se podrían añadir aquí
                    else:
                        print(f"No se encontró medicamento con ID {med_id}.")
                except ValueError:
                    print("ID inválido. Debe ser un número.")
                except Exception as e:
                    print(f"Error al obtener el medicamento: {e}")

            elif opcion_med == '3':
                # Listar todos los medicamentos
                try:
                    medicamentos = crud.obtener_medicamentos(db, limit=1000) # Aumentar límite si es necesario
                    if not medicamentos:
                        print("No hay medicamentos registrados.")
                    else:
                        _imprimir_subtitulo("Listado de Medicamentos")
                        print(f"{'ID':<5} | {'Nombre':<30} | {'Marca':<20} | {'Unidades/Caja':<15}")
                        print("-" * 75)
                        for med in medicamentos:
                            print(f"{med.id:<5} | {med.nombre:<30} | {(med.marca if med.marca else 'N/A'):<20} | {med.unidades_por_caja:<15}")
                except Exception as e:
                    print(f"Error al listar medicamentos: {e}")

            elif opcion_med == '4':
                # Actualizar medicamento
                try:
                    med_id_str = input("ID del medicamento a actualizar: ").strip()
                    if not med_id_str:
                        print("El ID no puede estar vacío.")
                        continue
                    med_id = int(med_id_str)
                    medicamento = crud.obtener_medicamento(db, med_id)
                    if not medicamento:
                        print(f"No se encontró medicamento con ID {med_id}.")
                        continue

                    print(f"Actualizando medicamento: {medicamento.nombre} (ID: {medicamento.id})")
                    print("Deje el campo en blanco si no desea cambiar el valor.")

                    nombre_nuevo = input(f"Nuevo nombre ({medicamento.nombre}): ").strip()
                    marca_nueva = input(f"Nueva marca ({medicamento.marca if medicamento.marca else 'N/A'}): ").strip()

                    unidades_nuevas_str = input(f"Nuevas unidades por caja ({medicamento.unidades_por_caja}): ").strip()
                    unidades_nuevas = None
                    if unidades_nuevas_str:
                        try:
                            unidades_nuevas = int(unidades_nuevas_str)
                            if unidades_nuevas <= 0:
                                print("Las unidades deben ser un número positivo. No se actualizará este campo.")
                                unidades_nuevas = medicamento.unidades_por_caja # Mantener valor anterior
                        except ValueError:
                            print("Unidades no válidas. No se actualizará este campo.")
                            unidades_nuevas = medicamento.unidades_por_caja # Mantener valor anterior

                    precio_nuevo_str = input(f"Nuevo precio de referencia ({medicamento.precio_por_caja_referencia if medicamento.precio_por_caja_referencia is not None else 'N/A'}): ").strip()
                    precio_nuevo = None
                    if precio_nuevo_str:
                        try:
                            precio_nuevo = float(precio_nuevo_str)
                        except ValueError:
                            print("Precio no válido. No se actualizará este campo.")
                            precio_nuevo = medicamento.precio_por_caja_referencia # Mantener valor anterior

                    datos_actualizacion = {}
                    if nombre_nuevo:
                        # Verificar que el nuevo nombre no exista ya (si es diferente al actual)
                        if nombre_nuevo.lower() != medicamento.nombre.lower():
                            existente = crud.obtener_medicamento_por_nombre(db, nombre=nombre_nuevo)
                            if existente and existente.id != med_id:
                                print(f"Error: Ya existe otro medicamento con el nombre '{nombre_nuevo}'. No se actualizará el nombre.")
                                nombre_nuevo = medicamento.nombre # Mantener nombre anterior
                            else:
                                datos_actualizacion['nombre'] = nombre_nuevo
                        else:
                             datos_actualizacion['nombre'] = nombre_nuevo # Mismo nombre, diferente capitalización

                    if marca_nueva:
                        datos_actualizacion['marca'] = marca_nueva
                    elif marca_nueva == "" and medicamento.marca is not None: # Si se ingresa vacío y antes había valor, se borra
                        datos_actualizacion['marca'] = None

                    if unidades_nuevas is not None and unidades_nuevas != medicamento.unidades_por_caja :
                        datos_actualizacion['unidades_por_caja'] = unidades_nuevas

                    if precio_nuevo is not None and precio_nuevo != medicamento.precio_por_caja_referencia:
                         datos_actualizacion['precio_por_caja_referencia'] = precio_nuevo
                    elif precio_nuevo_str == "" and medicamento.precio_por_caja_referencia is not None: # Si se ingresa vacío y antes había valor, se borra
                        datos_actualizacion['precio_por_caja_referencia'] = None


                    if datos_actualizacion:
                        crud.actualizar_medicamento(db, med_id, datos_actualizacion)
                        print(f"Medicamento ID {med_id} actualizado.")
                    else:
                        print("No se proporcionaron datos para actualizar.")

                except ValueError:
                    print("ID inválido. Debe ser un número.")
                except Exception as e:
                    print(f"Error al actualizar medicamento: {e}")

            elif opcion_med == '5':
                # Eliminar medicamento
                try:
                    med_id_str = input("ID del medicamento a eliminar: ").strip()
                    if not med_id_str:
                        print("El ID no puede estar vacío.")
                        continue
                    med_id = int(med_id_str)
                    medicamento = crud.obtener_medicamento(db, med_id)
                    if not medicamento:
                        print(f"No se encontró medicamento con ID {med_id}.")
                        continue

                    confirmacion = input(f"¿Está seguro de que desea eliminar '{medicamento.nombre}' (ID: {med_id})? Esto eliminará también todos sus lotes de stock y referencias en pedidos. (s/N): ").strip().lower()
                    if confirmacion == 's':
                        if crud.eliminar_medicamento(db, med_id):
                            print(f"Medicamento ID {med_id} eliminado correctamente.")
                        else:
                            print(f"No se pudo eliminar el medicamento ID {med_id}.") # Ya cubierto por el chequeo previo
                    else:
                        print("Eliminación cancelada.")
                except ValueError:
                    print("ID inválido. Debe ser un número.")
                except Exception as e:
                    print(f"Error al eliminar medicamento: {e}")

            elif opcion_med == '6':
                # Ver stock total y vencimiento próximo
                try:
                    med_id_str = input("ID del medicamento para ver stock/vencimiento: ").strip()
                    if not med_id_str:
                        print("El ID no puede estar vacío.")
                        continue
                    med_id = int(med_id_str)
                    medicamento = crud.obtener_medicamento(db, med_id)
                    if not medicamento:
                        print(f"No se encontró medicamento con ID {med_id}.")
                        continue

                    stock_total = crud.calcular_stock_total_unidades(db, med_id)
                    vencimiento_proximo = crud.calcular_fecha_vencimiento_proxima(db, med_id)

                    print(f"\n--- Stock y Vencimiento para: {medicamento.nombre} (ID: {med_id}) ---")
                    print(f"Stock Total (unidades activas): {stock_total}")
                    if vencimiento_proximo:
                        print(f"Fecha de Vencimiento Próxima (de lotes activos): {vencimiento_proximo.strftime('%d/%m/%Y')}")
                    else:
                        print("Fecha de Vencimiento Próxima: No hay lotes activos o con fecha de vencimiento.")

                except ValueError:
                    print("ID inválido. Debe ser un número.")
                except Exception as e:
                    print(f"Error al obtener stock/vencimiento: {e}")

            elif opcion_med == '0':
                break
            else:
                print("Opción no válida. Por favor, intente de nuevo.")

        if opcion_med != '0': # No pausar si va a salir del submenú
            input("\nPresione Enter para continuar...")


def _parse_date(date_str: str) -> Optional[date]:
    """Helper para parsear fechas en formato YYYY-MM-DD o DD/MM/YYYY."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            return None

def menu_stock():
    while True:
        _imprimir_subtitulo("Gestionar Stock (Lotes)")
        print("1. Añadir lote de stock a un medicamento")
        print("2. Listar lotes de un medicamento")
        print("3. Actualizar lote de stock")
        print("4. Eliminar lote de stock")
        print("0. Volver al menú principal")

        opcion_stock = input("Seleccione una opción: ").strip()

        with obtener_sesion_db() as db:
            if opcion_stock == '1':
                # Añadir lote de stock
                try:
                    med_id_str = input("ID del medicamento para añadir lote: ").strip()
                    if not med_id_str: print("ID de medicamento no puede estar vacío."); continue
                    med_id = int(med_id_str)

                    medicamento = crud.obtener_medicamento(db, med_id)
                    if not medicamento:
                        print(f"Medicamento con ID {med_id} no encontrado.")
                        continue

                    print(f"Añadiendo lote para: {medicamento.nombre}")

                    cajas_str = input("Cantidad de cajas: ").strip()
                    if not cajas_str: print("Cantidad de cajas no puede estar vacío."); continue
                    cantidad_cajas = int(cajas_str)
                    if cantidad_cajas <= 0: print("Cantidad de cajas debe ser positiva."); continue

                    unidades_lote_str = input(f"Unidades por caja para este lote (defecto: {medicamento.unidades_por_caja}): ").strip()
                    unidades_por_caja_lote = medicamento.unidades_por_caja
                    if unidades_lote_str:
                        unidades_por_caja_lote = int(unidades_lote_str)
                    if unidades_por_caja_lote <= 0: print("Unidades por caja debe ser positivo."); continue

                    fecha_venc_str = input("Fecha de vencimiento del lote (YYYY-MM-DD o DD/MM/YYYY): ").strip()
                    fecha_vencimiento = _parse_date(fecha_venc_str)
                    if not fecha_vencimiento:
                        print("Formato de fecha de vencimiento inválido.")
                        continue

                    fecha_compra_str = input(f"Fecha de compra (opcional, YYYY-MM-DD o DD/MM/YYYY, por defecto hoy): ").strip()
                    fecha_compra = _parse_date(fecha_compra_str) if fecha_compra_str else date.today()
                    if not fecha_compra: # Si se ingresó algo pero fue inválido
                         print("Formato de fecha de compra inválido, se usará la fecha de hoy.")
                         fecha_compra = date.today()


                    precio_lote_str = input("Precio de compra por caja para este lote (opcional): ").strip()
                    precio_lote = None
                    if precio_lote_str:
                        try:
                            precio_lote = float(precio_lote_str)
                        except ValueError:
                            print("Precio de lote no válido, se guardará sin precio.")

                    lote = crud.agregar_lote_stock(db, medicamento_id=med_id, cantidad_cajas=cantidad_cajas,
                                                   unidades_por_caja_lote=unidades_por_caja_lote,
                                                   fecha_vencimiento_lote=fecha_vencimiento,
                                                   fecha_compra_lote=fecha_compra,
                                                   precio_compra_lote_por_caja=precio_lote)
                    print(f"Lote ID {lote.id} añadido a '{medicamento.nombre}'. Total unidades en lote: {lote.unidades_totales_lote}")

                except ValueError:
                    print("Entrada inválida. Asegúrese de ingresar números donde corresponda.")
                except Exception as e:
                    print(f"Error al añadir lote: {e}")

            elif opcion_stock == '2':
                # Listar lotes de un medicamento
                try:
                    med_id_str = input("ID del medicamento para listar lotes: ").strip()
                    if not med_id_str: print("ID de medicamento no puede estar vacío."); continue
                    med_id = int(med_id_str)
                    medicamento = crud.obtener_medicamento(db, med_id)
                    if not medicamento:
                        print(f"Medicamento con ID {med_id} no encontrado.")
                        continue

                    solo_activos_str = input("¿Listar solo lotes activos (no vencidos)? (s/N): ").strip().lower()
                    solo_activos = solo_activos_str == 's'

                    lotes = crud.obtener_lotes_por_medicamento(db, med_id, solo_activos=solo_activos)
                    _imprimir_subtitulo(f"Lotes para: {medicamento.nombre} (ID: {med_id}) {'(Solo activos)' if solo_activos else ''}")
                    if not lotes:
                        print("No hay lotes registrados para este medicamento" + (" que cumplan el criterio de activos." if solo_activos else "."))
                    else:
                        print(f"{'Lote ID':<8} | {'Cajas':<7} | {'Uds/Caja':<10} | {'Total Uds':<10} | {'Compra':<12} | {'Vencimiento':<12} | {'Precio/Caja':<12}")
                        print("-" * 90)
                        for lote in lotes:
                            print(f"{lote.id:<8} | {lote.cantidad_cajas:<7} | {lote.unidades_por_caja_lote:<10} | "
                                  f"{lote.unidades_totales_lote:<10} | {lote.fecha_compra_lote.strftime('%d/%m/%Y'):<12} | "
                                  f"{lote.fecha_vencimiento_lote.strftime('%d/%m/%Y'):<12} | "
                                  f"{(lote.precio_compra_lote_por_caja if lote.precio_compra_lote_por_caja is not None else 'N/A'):<12}")
                except ValueError:
                    print("ID de medicamento inválido.")
                except Exception as e:
                    print(f"Error al listar lotes: {e}")

            elif opcion_stock == '3':
                # Actualizar lote de stock
                try:
                    lote_id_str = input("ID del lote a actualizar: ").strip()
                    if not lote_id_str: print("ID de lote no puede estar vacío."); continue
                    lote_id = int(lote_id_str)
                    lote = crud.obtener_lote_stock(db, lote_id)
                    if not lote:
                        print(f"Lote con ID {lote_id} no encontrado.")
                        continue

                    print(f"Actualizando Lote ID: {lote.id} (Medicamento: {lote.medicamento.nombre})")
                    print("Deje el campo en blanco si no desea cambiar el valor.")

                    datos_actualizacion = {}

                    cajas_str = input(f"Nueva cantidad de cajas ({lote.cantidad_cajas}): ").strip()
                    if cajas_str:
                        try:
                            datos_actualizacion['cantidad_cajas'] = int(cajas_str)
                            if datos_actualizacion['cantidad_cajas'] <= 0:
                                print("Cantidad debe ser positiva."); del datos_actualizacion['cantidad_cajas']
                        except ValueError: print("Cantidad inválida.")

                    unidades_lote_str = input(f"Nuevas unidades por caja ({lote.unidades_por_caja_lote}): ").strip()
                    if unidades_lote_str:
                        try:
                            datos_actualizacion['unidades_por_caja_lote'] = int(unidades_lote_str)
                            if datos_actualizacion['unidades_por_caja_lote'] <= 0:
                                print("Unidades deben ser positivas."); del datos_actualizacion['unidades_por_caja_lote']
                        except ValueError: print("Unidades inválidas.")

                    fecha_venc_str = input(f"Nueva fecha de vencimiento ({lote.fecha_vencimiento_lote.strftime('%Y-%m-%d')} YYYY-MM-DD o DD/MM/YYYY): ").strip()
                    if fecha_venc_str:
                        nueva_fecha_venc = _parse_date(fecha_venc_str)
                        if nueva_fecha_venc:
                            datos_actualizacion['fecha_vencimiento_lote'] = nueva_fecha_venc
                        else:
                            print("Formato de fecha de vencimiento inválido. No se actualizará.")

                    fecha_compra_str = input(f"Nueva fecha de compra ({lote.fecha_compra_lote.strftime('%Y-%m-%d')} YYYY-MM-DD o DD/MM/YYYY): ").strip()
                    if fecha_compra_str:
                        nueva_fecha_compra = _parse_date(fecha_compra_str)
                        if nueva_fecha_compra:
                            datos_actualizacion['fecha_compra_lote'] = nueva_fecha_compra
                        else:
                            print("Formato de fecha de compra inválido. No se actualizará.")

                    precio_lote_str = input(f"Nuevo precio de compra por caja ({lote.precio_compra_lote_por_caja if lote.precio_compra_lote_por_caja is not None else 'N/A'}): ").strip()
                    if precio_lote_str:
                        try:
                            datos_actualizacion['precio_compra_lote_por_caja'] = float(precio_lote_str)
                        except ValueError:
                            print("Precio no válido. No se actualizará.")
                    elif precio_lote_str == "" and lote.precio_compra_lote_por_caja is not None: # Borrar precio
                        datos_actualizacion['precio_compra_lote_por_caja'] = None

                    if datos_actualizacion:
                        crud.actualizar_lote_stock(db, lote_id, datos_actualizacion)
                        print(f"Lote ID {lote_id} actualizado.")
                    else:
                        print("No se proporcionaron datos para actualizar.")
                except ValueError:
                    print("ID de lote inválido.")
                except Exception as e:
                    print(f"Error al actualizar lote: {e}")

            elif opcion_stock == '4':
                # Eliminar lote de stock
                try:
                    lote_id_str = input("ID del lote a eliminar: ").strip()
                    if not lote_id_str: print("ID de lote no puede estar vacío."); continue
                    lote_id = int(lote_id_str)
                    lote = crud.obtener_lote_stock(db, lote_id)
                    if not lote:
                        print(f"Lote con ID {lote_id} no encontrado.")
                        continue

                    confirmacion = input(f"¿Está seguro de que desea eliminar el lote ID {lote_id} del medicamento '{lote.medicamento.nombre}' (Venc: {lote.fecha_vencimiento_lote.strftime('%d/%m/%Y')})? (s/N): ").strip().lower()
                    if confirmacion == 's':
                        if crud.eliminar_lote_stock(db, lote_id):
                            print(f"Lote ID {lote_id} eliminado.")
                        else: # Debería estar cubierto por la verificación anterior
                            print(f"No se pudo eliminar el lote ID {lote_id}.")
                    else:
                        print("Eliminación cancelada.")
                except ValueError:
                    print("ID de lote inválido.")
                except Exception as e:
                    print(f"Error al eliminar lote: {e}")

            elif opcion_stock == '0':
                break
            else:
                print("Opción no válida. Por favor, intente de nuevo.")

        if opcion_stock != '0':
            input("\nPresione Enter para continuar...")

def menu_pedidos():
    while True:
        _imprimir_subtitulo("Gestionar Pedidos")
        print("1. Crear nuevo pedido")
        print("2. Ver detalle de un pedido")
        print("3. Listar todos los pedidos")
        print("4. Añadir ítem a un pedido")
        print("5. Actualizar información de un pedido (estado, proveedor)")
        # Las opciones 6 y 7 (actualizar/eliminar item individual) se omiten por simplicidad actual
        print("8. Eliminar pedido completo")
        print("0. Volver al menú principal")

        opcion_pedido = input("Seleccione una opción: ").strip()

        with obtener_sesion_db() as db:
            if opcion_pedido == '1':
                # Crear nuevo pedido
                try:
                    fecha_pedido_str = input(f"Fecha del pedido (opcional, YYYY-MM-DD o DD/MM/YYYY, por defecto hoy): ").strip()
                    fecha_pedido = _parse_date(fecha_pedido_str) if fecha_pedido_str else date.today()
                    if not fecha_pedido: # Si se ingresó algo pero fue inválido
                         print("Formato de fecha de pedido inválido, se usará la fecha de hoy.")
                         fecha_pedido = date.today()

                    proveedor = input("Proveedor (opcional): ").strip()

                    # Listar estados disponibles
                    print("Estados de pedido disponibles:")
                    for estado_enum in models.EstadoPedido:
                        print(f"- {estado_enum.name} ({estado_enum.value})")

                    estado_str = input(f"Estado del pedido (por defecto: {models.EstadoPedido.PENDIENTE.value}): ").strip().upper()
                    estado = models.EstadoPedido.PENDIENTE
                    if estado_str:
                        try:
                            estado = models.EstadoPedido[estado_str]
                        except KeyError:
                            print(f"Estado '{estado_str}' no válido. Se usará '{models.EstadoPedido.PENDIENTE.value}'.")

                    pedido = crud.crear_pedido(db, fecha_pedido=fecha_pedido, proveedor=proveedor if proveedor else None, estado=estado)
                    print(f"Pedido ID {pedido.id} creado con fecha {pedido.fecha_pedido.strftime('%d/%m/%Y')} y estado '{pedido.estado.value}'.")
                    print("Ahora puede añadir ítems a este pedido usando la opción 'Añadir ítem a un pedido'.")

                except Exception as e:
                    print(f"Error al crear pedido: {e}")

            elif opcion_pedido == '2':
                # Ver detalle de un pedido
                try:
                    pedido_id_str = input("ID del pedido a ver: ").strip()
                    if not pedido_id_str: print("ID de pedido no puede estar vacío."); continue
                    pedido_id = int(pedido_id_str)
                    pedido = crud.obtener_pedido(db, pedido_id)
                    if not pedido:
                        print(f"Pedido con ID {pedido_id} no encontrado.")
                        continue

                    print(f"\n--- Detalle del Pedido ID: {pedido.id} ---")
                    print(f"Fecha: {pedido.fecha_pedido.strftime('%d/%m/%Y')}")
                    print(f"Proveedor: {pedido.proveedor if pedido.proveedor else 'N/A'}")
                    print(f"Estado: {pedido.estado.value}")

                    detalles = crud.obtener_detalles_por_pedido(db, pedido_id)
                    if not detalles:
                        print("Este pedido no tiene ítems.")
                    else:
                        print("Ítems del pedido:")
                        for det in detalles:
                            medicamento = crud.obtener_medicamento(db, det.medicamento_id) # Para mostrar nombre
                            nombre_med = medicamento.nombre if medicamento else f"ID Med: {det.medicamento_id}"
                            print(f"  - Ítem ID: {det.id}, Medicamento: {nombre_med}, "
                                  f"Cajas pedidas: {det.cantidad_cajas_pedidas}, "
                                  f"Precio/caja: {det.precio_unitario_compra_caja if det.precio_unitario_compra_caja is not None else 'N/A'}, "
                                  f"Subtotal: {det.subtotal_detalle:.2f}")

                    costo_total = crud.calcular_costo_total_pedido(db, pedido_id)
                    print(f"Costo Total del Pedido: {costo_total:.2f}")

                except ValueError:
                    print("ID de pedido inválido.")
                except Exception as e:
                    print(f"Error al ver detalle del pedido: {e}")

            elif opcion_pedido == '3':
                # Listar todos los pedidos
                try:
                    pedidos = crud.obtener_pedidos(db, limit=1000) # Aumentar límite si es necesario
                    if not pedidos:
                        print("No hay pedidos registrados.")
                    else:
                        _imprimir_subtitulo("Listado de Pedidos")
                        print(f"{'ID':<5} | {'Fecha':<12} | {'Proveedor':<25} | {'Estado':<15} | {'Costo Total':<12}")
                        print("-" * 80)
                        for p in pedidos:
                            costo_total_calc = crud.calcular_costo_total_pedido(db, p.id)
                            print(f"{p.id:<5} | {p.fecha_pedido.strftime('%d/%m/%Y'):<12} | "
                                  f"{(p.proveedor if p.proveedor else 'N/A'):<25} | {p.estado.value:<15} | "
                                  f"{costo_total_calc:<12.2f}")
                except Exception as e:
                    print(f"Error al listar pedidos: {e}")

            elif opcion_pedido == '4':
                # Añadir ítem a un pedido
                try:
                    pedido_id_str = input("ID del pedido para añadir ítem: ").strip()
                    if not pedido_id_str: print("ID de pedido no puede estar vacío."); continue
                    pedido_id = int(pedido_id_str)
                    pedido = crud.obtener_pedido(db, pedido_id)
                    if not pedido:
                        print(f"Pedido con ID {pedido_id} no encontrado.")
                        continue
                    if pedido.estado != models.EstadoPedido.PENDIENTE:
                        print(f"No se pueden añadir ítems a un pedido que no esté en estado '{models.EstadoPedido.PENDIENTE.value}'. Estado actual: {pedido.estado.value}")
                        continue

                    med_id_str = input("ID del medicamento a añadir al pedido: ").strip()
                    if not med_id_str: print("ID de medicamento no puede estar vacío."); continue
                    med_id = int(med_id_str)
                    medicamento = crud.obtener_medicamento(db, med_id)
                    if not medicamento:
                        print(f"Medicamento con ID {med_id} no encontrado.")
                        continue

                    print(f"Añadiendo '{medicamento.nombre}' al pedido ID {pedido_id}")

                    cajas_str = input("Cantidad de cajas pedidas: ").strip()
                    if not cajas_str: print("Cantidad de cajas no puede estar vacío."); continue
                    cantidad_cajas = int(cajas_str)
                    if cantidad_cajas <= 0: print("Cantidad de cajas debe ser positiva."); continue

                    precio_caja_str = input(f"Precio de compra por caja para este ítem (opcional, ej: {medicamento.precio_por_caja_referencia if medicamento.precio_por_caja_referencia else '10.00'}): ").strip()
                    precio_caja = None
                    if precio_caja_str:
                        try:
                            precio_caja = float(precio_caja_str)
                        except ValueError:
                            print("Precio no válido, se guardará sin precio específico para este ítem del pedido.")

                    detalle = crud.agregar_detalle_pedido(db, pedido_id=pedido_id, medicamento_id=med_id,
                                                          cantidad_cajas_pedidas=cantidad_cajas,
                                                          precio_unitario_compra_caja=precio_caja)
                    print(f"Ítem ID {detalle.id} ('{medicamento.nombre}') añadido al pedido ID {pedido_id}.")

                except ValueError:
                    print("Entrada inválida. Asegúrese de ingresar números donde corresponda.")
                except Exception as e:
                    print(f"Error al añadir ítem al pedido: {e}")

            elif opcion_pedido == '5':
                # Actualizar información de un pedido (estado, proveedor)
                try:
                    pedido_id_str = input("ID del pedido a actualizar: ").strip()
                    if not pedido_id_str: print("ID de pedido no puede estar vacío."); continue
                    pedido_id = int(pedido_id_str)
                    pedido = crud.obtener_pedido(db, pedido_id)
                    if not pedido:
                        print(f"Pedido con ID {pedido_id} no encontrado.")
                        continue

                    print(f"Actualizando Pedido ID: {pedido.id} (Fecha: {pedido.fecha_pedido.strftime('%d/%m/%Y')})")
                    print("Deje el campo en blanco si no desea cambiar el valor.")
                    datos_actualizacion = {}

                    nuevo_proveedor = input(f"Nuevo proveedor ({pedido.proveedor if pedido.proveedor else 'N/A'}): ").strip()
                    if nuevo_proveedor:
                        datos_actualizacion['proveedor'] = nuevo_proveedor
                    elif nuevo_proveedor == "" and pedido.proveedor is not None: # Borrar proveedor
                        datos_actualizacion['proveedor'] = None

                    print("Estados de pedido disponibles:")
                    for estado_enum in models.EstadoPedido:
                        print(f"- {estado_enum.name} ({estado_enum.value})")
                    nuevo_estado_str = input(f"Nuevo estado ({pedido.estado.value}): ").strip().upper()
                    if nuevo_estado_str:
                        try:
                            datos_actualizacion['estado'] = models.EstadoPedido[nuevo_estado_str]
                        except KeyError:
                            print(f"Estado '{nuevo_estado_str}' no válido. No se actualizará el estado.")

                    if datos_actualizacion:
                        crud.actualizar_pedido(db, pedido_id, datos_actualizacion)
                        print(f"Pedido ID {pedido_id} actualizado.")
                    else:
                        print("No se proporcionaron datos para actualizar.")
                except ValueError:
                    print("ID de pedido inválido.")
                except Exception as e:
                    print(f"Error al actualizar pedido: {e}")

            elif opcion_pedido == '8':
                # Eliminar pedido completo
                try:
                    pedido_id_str = input("ID del pedido a eliminar: ").strip()
                    if not pedido_id_str: print("ID de pedido no puede estar vacío."); continue
                    pedido_id = int(pedido_id_str)
                    pedido = crud.obtener_pedido(db, pedido_id)
                    if not pedido:
                        print(f"Pedido con ID {pedido_id} no encontrado.")
                        continue

                    confirmacion = input(f"¿Está seguro de que desea eliminar el pedido ID {pedido_id} (Fecha: {pedido.fecha_pedido.strftime('%d/%m/%Y')})? Esto eliminará también todos sus ítems. (s/N): ").strip().lower()
                    if confirmacion == 's':
                        if crud.eliminar_pedido(db, pedido_id):
                            print(f"Pedido ID {pedido_id} eliminado.")
                        else: # Cubierto por chequeo previo
                            print(f"No se pudo eliminar el pedido ID {pedido_id}.")
                    else:
                        print("Eliminación cancelada.")
                except ValueError:
                    print("ID de pedido inválido.")
                except Exception as e:
                    print(f"Error al eliminar pedido: {e}")

            elif opcion_pedido == '0':
                break
            else:
                print("Opción no válida. Por favor, intente de nuevo.")

        if opcion_pedido != '0':
            input("\nPresione Enter para continuar...")


if __name__ == "__main__":
    # Pequeña validación para la creación de la base de datos la primera vez
    # Esto es para que el mensaje de creación de BD no aparezca siempre si ya existe.
    # Ahora usamos DATABASE_FILE_PATH directamente desde database.py

    # Asegurarse de que el directorio de datos exista (aunque database.py ya lo hace,
    # es bueno tenerlo aquí por si create_db_and_tables no se llamara explícitamente antes)
    if not os.path.exists(database.DATA_DIR):
        os.makedirs(database.DATA_DIR)
        print(f"Directorio '{database.DATA_DIR}' creado.")

    if not os.path.exists(database.DATABASE_FILE_PATH):
        print(f"Base de datos no encontrada en {database.DATABASE_FILE_PATH}, inicializando...")
        # database.create_db_and_tables() crea el directorio Y las tablas.
        database.create_db_and_tables()
    else:
        # Si la base de datos ya existe, solo nos aseguramos que las tablas estén ahí.
        # Base.metadata.create_all es seguro de llamar múltiples veces y no recreará tablas.
        print(f"Usando base de datos existente: {database.DATABASE_FILE_PATH}")
        database.Base.metadata.create_all(bind=database.engine) # Solo crea tablas si no existen
    main()
