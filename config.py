import pyodbc
import time

SECRET_KEY = 'B!1w8NAt1T^%kvhUI*S^'

# Configuración de la conexión
server = '10.10.10.247'
database = 'SICMA'
username = 'CrystalUser'
password = 'CrystalUser'

# Cadena de conexión
connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};'

def conectar_bd():
    while True:
        try:
            # Intentar establecer la conexión
            connection = pyodbc.connect(connection_string)
            return connection

        except pyodbc.Error as e:
            # Registrar el error
            print(f"Error de base de datos: {e}")
            print("Intentando reconectar...")
            time.sleep(5)  # Pausa antes de intentar reconectar (puedes ajustar el tiempo de espera)