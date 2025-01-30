import pyodbc

from models.config import conectar_bd

def obtener_datos_prestamos(fecha_inicio):
    # Ejecutar la consulta
    connection = conectar_bd()
    if connection:
            try:
                cursor = connection.cursor()          
                sql = """SELECT  dbo.g_cliente.nro_documento, dbo.g_cliente.nombre, dbo.g_cliente.cod_cliente, dbo.p_desembolso_prestamo.nro_prestamo, 
                            cast((dbo.p_maestro_prestamo.monto_cuota_inicial)/10 as int) as monto_cuota,
                            FORMAT(dbo.p_maestro_prestamo.fecha_ult_desembolso, 'dd/MM/yyyy') AS fecha_desembolso
                        FROM  dbo.g_cliente
                        INNER JOIN dbo.p_maestro_prestamo ON dbo.g_cliente.cod_cliente = dbo.p_maestro_prestamo.cod_cliente  
                        INNER JOIN dbo.p_tipo_credito ON dbo.p_maestro_prestamo.cod_tipo_credito = dbo.p_tipo_credito.cod_tipo_credito 
                        INNER JOIN dbo.g_moneda ON dbo.p_maestro_prestamo.cod_moneda = dbo.g_moneda.cod_moneda 
                        INNER JOIN dbo.p_desembolso_prestamo ON dbo.p_maestro_prestamo.nro_prestamo = dbo.p_desembolso_prestamo.nro_prestamo 
                        INNER JOIN dbo.g_sucursal ON dbo.p_maestro_prestamo.cod_sucursal = dbo.g_sucursal.cod_sucursal
                        left join p_solicitud_credito sc on sc.nro_solicitud=p_maestro_prestamo.nro_solicitud
                        where dbo.p_maestro_prestamo.fecha_ult_desembolso = ?
                        order by dbo.g_cliente.cod_cliente"""
                cursor.execute(sql, fecha_inicio)
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