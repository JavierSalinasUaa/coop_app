import mysql.connector
from mysql.connector import Error

# Configuración de conexión a la base de datos
db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'gestion_prestamo'
}

def probar_conexion():
    try:
        # Establecer la conexión
        conexion = mysql.connector.connect(**db_config)

        # Verificar si la conexión es exitosa
        if conexion.is_connected():
            return conexion
    except Error as e:
        print("Error en la conexión a la base de datos:", e)

def buscarPrestamo(fecha_solicitud, fecha_fin):
        connection = probar_conexion()
        try:
                cursor = connection.cursor()          
                sql = """SELECT pm.*, es.descripcion FROM maestro_prestamo pm
                INNER JOIN estado es
                on es.estado_id = pm.estado
                 WHERE pm.fecha_solic_prestamo BETWEEN %s AND %s"""
                cursor.execute(sql, (fecha_solicitud, fecha_fin))
                rows = cursor.fetchall()    
                if not rows:
                    print("Sin Datos")
                else:
                    return rows                
        except  mysql.connector.Error as e:
                # Maneja el error y reconecta
                print(f"Error de base de datos: {e}")
        finally:
                cursor.close()
                connection.close()

def guardarPrestamo(nro_prestamo, cod_cliente, fecha_solicitud, fecha_recepcion, monto_pre, usuario_des, usuario_receptor, estado, solicitado_por = None):
        # Inserción en la base de datos
        conexion = probar_conexion()
        cursor = conexion.cursor()

        try:
            query = """
                INSERT INTO maestro_prestamo (nro_prestamo, cod_cliente, fecha_solic_prestamo, fecha_recepcion, monto_prestamo, usuario_desembolso, usuario_receptor, estado, solicitud_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (nro_prestamo, cod_cliente, fecha_solicitud, fecha_recepcion, monto_pre, usuario_des, usuario_receptor, estado, solicitado_por))
            conexion.commit()
            exito = True
            return exito
        except mysql.connector.Error as err:            
            exito = False
            print(f"Error en la base de datos: {err}")
            return exito
        finally:
            cursor.close()
            conexion.close()

def updatePrestamo(nro_prestamo, estado, usuario, solicitado_por = None):
    # Conexión a la base de datos
    conexion = probar_conexion()
    cursor = conexion.cursor()
    try:
        # Obtener el estado actual del préstamo antes de la actualización
        cursor.execute("SELECT estado FROM maestro_prestamo WHERE nro_prestamo=%s", (nro_prestamo,))
        resultado = cursor.fetchone()
        if not resultado:
            return 1  # No se encontró el préstamo
        
        estado_anterior = resultado[0]

        if estado_anterior == int(estado):
             return 2

        # Actualizar el estado del préstamo
        query = """
            UPDATE maestro_prestamo
            SET estado=%s, solicitud_usuario=%s
            WHERE nro_prestamo=%s
        """
        valores = (estado, solicitado_por, nro_prestamo)
        cursor.execute(query, valores)
        conexion.commit()

        # Verificar si se actualizó alguna fila
        if cursor.rowcount > 0:
            # Insertar el cambio en el historial
            query_historial = """
                INSERT INTO histo_movimiento (nro_prestamo, solicitud_usuario, estado_anterior, estado_nuevo, usuario)
                VALUES (%s, %s, %s, %s, %s)
            """
            valores_historial = (nro_prestamo, solicitado_por, estado_anterior, estado, usuario)
            cursor.execute(query_historial, valores_historial)
            conexion.commit()
            
            return 3  # Actualización y registro exitosos
        else:
            return 4  # No se actualizó ninguna fila
    except mysql.connector.Error as error:
        print(f"Error en la actualización: {error}")
        return 5  # Error en la actualización
    finally:
        cursor.close()
        conexion.close()


def eliminarPrestamo(nro_prestamo):
        # Inserción en la base de datos
        conexion = probar_conexion()
        cursor = conexion.cursor()
        try:
            query = """
                DELETE FROM maestro_prestamo
                WHERE nro_prestamo=%s
            """
            cursor.execute(query, (nro_prestamo,))
            conexion.commit()
            # Opcional: verificar si se actualizó alguna fila
            if cursor.rowcount > 0:
                return True  # Actualización exitosa
            else:
                return False  # No se encontró ninguna fila con ese ID
        except mysql.connector.Error as error:            
            print(f"Error al eliminar: {error}")
            return False  # Error en la actualización
        finally:
            cursor.close()
            conexion.close()

def buscarEstados():
    conexion = probar_conexion()
    try:
        cursor = conexion.cursor()          
        sql = """SELECT * FROM estado"""
        cursor.execute(sql)
        rows = cursor.fetchall()   
        if not rows:
            return None
        else:
             return rows
    finally:
        cursor.close()
        conexion.close()

def verificar_existencia(nro_prestamo):
    conexion = probar_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT 1 FROM maestro_prestamo WHERE nro_prestamo = %s", (nro_prestamo,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conexion.close()

def ver_historial_prestamo(nro_prestamo):
    conexion = probar_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("""SELECT hm.*, es.descripcion, ess.descripcion FROM histo_movimiento hm
                            INNER JOIN estado es 
                            on es.estado_id = hm.estado_anterior
                            INNER JOIN estado ess
                            on ess.estado_id = hm.estado_nuevo
                            WHERE nro_prestamo =%s
                            order by hm.fecha_mod desc""", (nro_prestamo,))
        rows = cursor.fetchall()   
        if not rows:
            return None
        else:
            return rows
    finally:
        cursor.close()
        conexion.close()