import pyodbc

from models.config import conectar_bd

def obtener_datos_solicitud_prestamo(fecha_solicitud_ini, fecha_solicitud_fin, id_user=None):
    # Ejecutar la consulta
    connection = conectar_bd()
    if connection:
            try:
                cursor = connection.cursor()          
                sql = """select dbo.[fnCUENTA_OPERATIVA](pm.nro_prestamo) as nro_prestamo, pm.fecha_ult_desembolso,  gc.cod_cliente, pm.importe_prestamo, gc.nombre as titular, su.nombre as encargado
                            from p_maestro_prestamo pm
                            inner join g_cliente gc
                            on gc.cod_cliente = pm.cod_cliente
                            inner join s_usuario su
                            on su.id_usuario = pm.usuario_insert
                            where pm.fecha_ult_desembolso BETWEEN ? AND ?"""
                # Lista de parámetros, `fecha_solicitud` es el primero
                parametros = [fecha_solicitud_ini, fecha_solicitud_fin]
                
                # Agrega la condición de `usuario` si está definida
                if id_user:
                    sql += " AND su.id_usuario = ?"
                    parametros.append(id_user)
                #Agregar ordenamiento
                sql += " order by nro_prestamo"
                
                # Ejecuta la consulta con los parámetros adecuados
                cursor.execute(sql, parametros)
                rows = cursor.fetchall()

                # Convierte cada fila en un diccionario    
                columns = [column[0] for column in cursor.description]  # Extrae los nombres de las columnas
                result = [dict(zip(columns, row)) for row in rows]  # Crea una lista de diccionarios
            
                if not result:
                    None
                else:
                    return result  # Devuelve la lista de diccionarios
                
            except pyodbc.Error as e:
                # Maneja el error y reconecta
                print(f"Error de base de datos: {e}")
            finally:
                cursor.close()
                connection.close()

def buscarUsuarios():
         # Ejecutar la consulta
    connection = conectar_bd()
    if connection:
            try:
                cursor = connection.cursor()          
                sql = """select id_usuario, nombre from s_usuario"""
                cursor.execute(sql)
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

def buscarRol(nombre):
         # Ejecutar la consulta
    connection = conectar_bd()
    if connection:
            try:
                cursor = connection.cursor()          
                sql = """SELECT sp.descripcion from s_perfiles sp 
                         right join s_usuario su 
                         on su.cod_perfil = sp.cod_perfil
                         where su.nombre = ?"""
                cursor.execute(sql, nombre)
                rows = cursor.fetchall()
            
                if not rows:
                    print("Sin Datos")
                    return None
                else:
                    return rows
                
            except pyodbc.Error as e:
                # Maneja el error y reconecta
                print(f"Error de base de datos: {e}")
            finally:
                cursor.close()
                connection.close()