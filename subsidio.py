from config import conectar_bd
import pyodbc

def obtener_datos_subsidio(id_buscar):
    # Ejecutar la consulta
    connection = conectar_bd()
    if connection:
            try:
                cursor = connection.cursor()          
                sql = """SELECT ds.cod_cliente, ds.nro_solicitud, ds.fecha_solic, dts.descripcion, gc.nombre, gc.nro_documento
                            from d_solicitud_beneficio ds 
                            inner join g_cliente gc
                            on gc.cod_cliente = ds.cod_cliente
                            inner join d_tipo_subsidio dts
                            on dts.cod_tipo_subsidio = ds.cod_tipo_subsidio
                            where ds.cod_cliente=? order by ds.nro_solicitud"""
                cursor.execute(sql, id_buscar)
                rows = cursor.fetchall()    
                if not rows:
                    print("Sin Datos")
                else:
                    return rows
                
            except pyodbc.Error as e:
                # Maneja el error y reconecta
                print(f"Error de base de datos: {e}")
            finally:
                cursor.close()
                connection.close()