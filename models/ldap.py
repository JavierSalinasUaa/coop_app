from flask_login import login_user
from flask import session
from ldap3 import Server, Connection, ALL, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPBindError
from models.entities.User import Usuario
from models.source_prestamo import buscarRol

def obtenerdatos(usuario, contrasena):
# Configura la conexión LDAP
    server = Server('ldap://10.10.10.240', get_info=ALL)

    # Reemplaza 'your_domain' y 'your_username' con los valores adecuados
    bind_dn = 'buencamino\\' + usuario

    # Intenta autenticar al usuario
    try:
        # Intenta conectarte al servidor LDAP
            with Connection(server, user=bind_dn, password=contrasena, authentication=NTLM) as conn:
                if conn.bind():
                    rolUser = buscarRol(usuario)                    
                    result = rolUser[0][0] if rolUser else None
                    session['role'] = result
                    usuario_obj = Usuario(user_id=usuario, username=usuario, role=result)
                    login_user(usuario_obj)
                    return True
                else:
                    return False
    except TypeError as e:
        mensaje = "Error al autenticar"
        print(mensaje + f" {e}")
        return False

    except LDAPBindError as e:
        mensaje = "Error al autenticar"
        print(mensaje + f" {e}")
        return False