from errno import errorcode
from functools import wraps
from logging.handlers import TimedRotatingFileHandler
import traceback
from flask import Flask, jsonify, render_template, request, redirect, session, url_for, flash
from flask_login import LoginManager, current_user, login_required, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from datetime import datetime, timedelta
from ldap import obtenerdatos
from mysql_config import guardarPrestamo, buscarPrestamo, buscarEstados, eliminarPrestamo, updatePrestamo, verificar_existencia, ver_historial_prestamo
from walton import obtener_datos_prestamos
from subsidio import obtener_datos_subsidio
from prestamo import obtener_datos_solicitud_prestamo, buscarUsuarios
from models.entities.User import Usuario
from reportes.reporte_subsidio import report
from reportes.reporte_walton import reporte
from reportes.reporte_cambiosPrestamo import reporteCamb
from reportes.reporte_filtros import reporteFiltro
import schedule
import time
import os
import sys
import logging
import threading

app = Flask(__name__)


app.secret_key = 'B!1w8NAt1T^%kvhUI*S^'
app.config['SESSION_TYPE'] = 'filesystem'

app.register_blueprint(report, url_prefix='/reporte')
app.register_blueprint(reporte, url_prefix='/reporteWalton')
app.register_blueprint(reporteCamb, url_prefix='/reporteCamb')
app.register_blueprint(reporteFiltro, url_prefix='/reporteFiltros')

csrf = CSRFProtect()

login_manager = LoginManager(app)
login_manager.login_view = 'login'
Session(app)

TIEMPO_INACTIVIDAD_SEGUNDOS = 300  # 5 minutos

# Obtener la fecha actual
current_date = datetime.now().strftime("%Y-%m-%d")

# Configurar el logger con TimedRotatingFileHandler
log_file_name = 'server_log'
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Crear el manejador rotativo por día
handler = TimedRotatingFileHandler(filename=f'{log_file_name}.log', when="midnight", interval=1, backupCount=5)
handler.setFormatter(log_formatter)

# Configurar el logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Decorador para capturar eventos antes de la solicitud
@app.before_request
def log_before_request():
    app.logger.info('%s', request.path)

def role_required(required_role=[]):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rol_usuario = session.get('role')
            if not current_user.is_authenticated or rol_usuario not in required_role:
                flash("No tienes permiso para acceder a esta página.", "error")
                # Redirige a la página anterior o a la página de inicio si no se encuentra referrer
                return redirect(request.referrer or '/')
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# Decorador para capturar eventos después de la solicitud
@app.after_request
def log_after_request(response):
    app.logger.info('%s', request.path)
    return response

# Decorador para capturar eventos de error
@app.errorhandler(Exception)
def log_exception(error):
    app.logger.error('Error durante la solicitud: %s', str(error))
    return 'Error interno del servidor', 500

@app.route('/')
def inicio():
    if current_user.is_authenticated:        
        return render_template('index.html')
    return render_template('login_domain.html')
    

@app.route('/login')
def login():
    return render_template('login_domain.html')

@app.route('/prestamo_detalle')
@role_required({'ARCHIVO', 'ADMINISTRADOR', 'CREDITO'})
def prestamo():
    session['prestamos'] = ''
    session['prestamos_por_fecha'] = {}
    rows = buscarEstados()
    filas = buscarUsuarios()
    rol_usuario = session.get('role')

    # Pasar los datos de `estado` a la plantilla
    return render_template('prestamo_detalle.html', estados=rows, usuarios=filas, roles = rol_usuario)

@login_manager.user_loader
def cargar_usuario(user_id):
    # Implementa la lógica para cargar el usuario desde tu sistema
    return Usuario(user_id, user_id)

@app.route('/login_dom', methods=['GET', 'POST'])
def login_dom():
    if request.method == 'POST':
        user = request.form['usuario']
        passw = request.form['contrasena']

        data = obtenerdatos(user, passw)
        if data:
            next_url = session.get('next')
            if next_url:
                session.pop('next')  # Eliminate the next URL from the session
                return redirect(next_url)
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrecto")
            return render_template('login_domain.html')
        
@app.route('/subsidio')
@login_required
def subsidio():
    session['clientes'] = ''
    return render_template('subsidio.html')

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/walton')
@login_required
def walton():
    return render_template('walton.html')


@app.route('/logout')
def cerrar_sesion():
        logout_user()
        session.clear()
        flash('Has cerrado sesión exitosamente.')
        return redirect(url_for('login'))

@app.before_request
def before_request():
    # Verifica si el usuario está autenticado y ha pasado el tiempo de inactividad
    if current_user.is_authenticated:
        ultima_actividad = session.get('ultima_actividad')
        if ultima_actividad and datetime.utcnow() - ultima_actividad > timedelta(seconds=TIEMPO_INACTIVIDAD_SEGUNDOS):
            logger.info('Sesion cerrada por inactividad para: %s', current_user.username)
            flash('Tu sesión se cerró automáticamente por inactividad. Por favor, inicia sesión nuevamente.', 'info')
            session['next'] = request.url
            logout_user()
            return redirect(url_for('login'))
    session['ultima_actividad'] = datetime.utcnow()

@app.route('/guardarPrestamos', methods=['POST'])
def guardar_prestamos():
    try:
        # Capturar los datos enviados desde el frontend
        prestamos = request.form.getlist('prestamos')  # Obtenemos la lista de préstamos seleccionados

        if not prestamos:
            return jsonify({"message": "No se recibieron datos para guardar."}), 400

        resultados = []
        for prestamo_str in prestamos:
            # Decodificar cada registro JSON (se espera que el frontend envíe JSON como strings dentro de la lista)
            prestamo = eval(prestamo_str)

            data = verificar_existencia(prestamo['nro_prestamo'])  # Aquí llamas a tu función de verificación
            if data:
                # Si existe, devolver un mensaje de error
                return jsonify(message="Error: Clave duplicada del préstamo nro: " + prestamo['nro_prestamo']), 400

            # Llamar a la función `guardarPrestamo`
            exito = guardarPrestamo(
                nro_prestamo=prestamo['nro_prestamo'],
                cod_cliente=prestamo['cod_cliente'],
                fecha_solicitud=prestamo['fecha_solicitud_pre'],
                fecha_recepcion=prestamo['fecha_recepcion'],
                monto_pre=prestamo['monto_pre'],
                usuario_des=prestamo['usuario_des'],
                usuario_receptor=prestamo['usuario_receptor'],
                estado=prestamo['estado'],
                solicitado_por=prestamo.get('solicitado_por', None)
            )

            resultados.append({"nro_prestamo": prestamo['nro_prestamo'], "exito": exito})

        # Verificar si todos los registros se guardaron correctamente
        if all(r['exito'] for r in resultados):
            return jsonify({"message": f"Se guardaron {len(prestamos)} préstamos correctamente."})
        else:
            return jsonify({"message": "Algunos registros no se pudieron guardar.", "resultados": resultados}), 207

    except Exception as e:
        return jsonify({"message": f"Error al procesar los préstamos: {str(e)}"}), 500

@app.route('/guardarPre', methods=['POST'])
def guardarPre():
    action_type = request.form.get('actionType')
    usuario_receptor = request.form['usuario_receptor']
    cod_cliente = request.form['cod_cliente']
    fecha_recepcion = request.form['fecha_recepcion']
    nro_prestamo = request.form['nro_prestamo']
    monto_pre = request.form['monto_pre']
    usuario_des = request.form['usuario_des']
    estado = request.form['estado']
    solicitado_por = request.form['userss']

    if action_type == 'insert':
        data = verificar_existencia(nro_prestamo)
        if data:
            return jsonify(success=False, message="Error: Clave duplicada del prestamo nro: " + nro_prestamo)
        rows = guardarPrestamo(nro_prestamo, cod_cliente, fecha_recepcion, monto_pre, usuario_des, usuario_receptor, estado, solicitado_por)
        if rows:
            flash("Préstamo guardado exitosamente.", "success")
            return jsonify(success=True, redirect_url=url_for('prestamo'))
        else:
            return jsonify(success=False, message="Error: No se ha encontrado el prestamo.")

    elif action_type == 'update':
        rows = updatePrestamo(nro_prestamo, estado, usuario_receptor, solicitado_por)
        if rows == 3:
            return jsonify(success=True, message="Préstamo actualizado exitosamente.")
        elif rows == 4:
            return jsonify(success=False, message="No hay ninguna modificación.")
        elif rows == 2:
            return jsonify(success=False, message="Debe cambiar el estado.")
        else:
            return jsonify(success=False, message="Ocurrió un error.")


@app.route('/borrarPre', methods=['GET', 'POST'])
def borrarPre():
    if request.method == 'POST':
        nro_prestamo = request.form['nro_prestamo']
    row = eliminarPrestamo(nro_prestamo)

    if row:
        flash("Préstamo eliminado exitosamente.", "success")
        return jsonify({"status": "success", "redirect_url": url_for('prestamo')})
    else:
        return jsonify({"status": "error", "message": "No se pudo eliminar el préstamo."})

@app.route('/historialPre', methods=['GET', 'POST'])
def historialPre():
    if request.method == 'POST':
        nro_prestamo = request.form['nro_prestamo']
    row = ver_historial_prestamo(nro_prestamo)

    if row:
        session['prestamos'] = row
        return jsonify({"status": "success", "redirect_url": url_for('reporteCamb.reporteCambios')})
    else:
        return jsonify({"status": "error", "message": "No se encontraron cambios."})
    
@app.route('/filtrosPre', methods=['GET', 'POST'])
def filtrosPre():
        # Validar si 'fecha_solicitud' está presente
        data = request.get_json()
        fecha_solicitud_ini = data.get('fecha_solicitud_ini')
        fecha_solicitud_hasta = data.get('fecha_solicitud_hasta')
        if not fecha_solicitud_ini or not fecha_solicitud_hasta:
            return jsonify({"error": "La fecha de solicitud es obligatoria"}), 400

        # Formatear la fecha
        fecha_solicitud_fmt = datetime.strptime(fecha_solicitud_ini, '%Y-%m-%d')
        fecha_solicitud_formateada = fecha_solicitud_fmt.strftime('%d/%m/%Y')

        fecha_solicitud_fin_fmt = datetime.strptime(fecha_solicitud_hasta, '%Y-%m-%d')
        fecha_solicitud_fin_formateada = fecha_solicitud_fin_fmt.strftime('%d/%m/%Y')
        user = data.get('users')

        # Obtener los datos
        rows = obtener_datos_solicitud_prestamo(fecha_solicitud_formateada, fecha_solicitud_fin_formateada, user)
        # Agrupar por fecha

        if not rows:
            return jsonify({"error": "No se encontraron resultados para la búsqueda."}), 400  

        for prestamo in rows:
            nro_prestamo = prestamo["nro_prestamo"]
            prestamo["existe"] = verificar_existencia(nro_prestamo)  # True o False según la verificación                

        prestamos_por_fecha = {}
        prestamos_por_fecha_rep = {}
        session['prestamos_por_fecha'] = {}
        for fila in rows:
            try:
                # Intentar acceder a la columna 'fecha_ult_desembolso'
                fecha = str(fila['fecha_ult_desembolso'])  # Convertir fecha a string para JSON
                if fecha not in prestamos_por_fecha:
                    prestamos_por_fecha[fecha] = []
                    prestamos_por_fecha_rep[fecha] = []
                prestamos_por_fecha[fecha].append(fila)                
                try:                 
                    if (fila['existe'] == False):
                        prestamos_por_fecha_rep[fecha].append(fila)
                        session['prestamos_por_fecha'] = prestamos_por_fecha_rep  
                except Exception as e:
                    print(f"Error inesperado: {str(e)}")
                    print("Detalles del error:")
                    traceback.print_exc()
            except KeyError:
                # Manejar el caso en que la columna no exista
                print("Error: La columna 'fecha_ult_desembolso' no existe en los datos.")
                return jsonify({"error": "La columna 'fecha_ult_desembolso' no está presente en los resultados."}), 500
            except Exception as e:
                # Manejar cualquier otro error inesperado
                print(f"Error inesperado al procesar la fila: {str(e)}")
                return jsonify({"error": "Ocurrió un error al procesar los datos."}), 500
                    
        return jsonify(prestamos_por_fecha)

@app.route('/buscarPrestamo', methods=['POST'])
def buscar_datos():
        # Validar si 'fecha_solicitud' está presente
        fecha_solicitud = request.form.get('fecha_solicitud')
        fecha_solicitud_fin = request.form.get('fecha_solicitud_fin')
        if not fecha_solicitud:
            return jsonify({"error": "La fecha de solicitud es obligatoria"}), 400

        # Formatear la fecha
        fecha_solicitud_fmt = datetime.strptime(fecha_solicitud, '%Y-%m-%d')
        fecha_solicitud_formateada = fecha_solicitud_fmt.strftime('%d/%m/%Y')

        fecha_solicitud_fin_fmt = datetime.strptime(fecha_solicitud_fin, '%Y-%m-%d')
        fecha_solicitud_fin_formateada = fecha_solicitud_fin_fmt.strftime('%d/%m/%Y')
        user = request.form.get('users')

        # Obtener los datos
        rows = obtener_datos_solicitud_prestamo(fecha_solicitud_formateada, fecha_solicitud_fin_formateada, user)

        if not rows:
            return jsonify({"message": "No se encontraron resultados para la búsqueda."}), 400
            
        data = []
        for prestamos in rows:
            dat = verificar_existencia(prestamos["nro_prestamo"])
            if dat:
                data.append(prestamos["nro_prestamo"])

        return jsonify({"prestamos": rows, "datas": data})

@app.route('/buscarPre', methods= ['POST', 'GET'])
@login_required
def buscarPre():
    id_buscar = request.form.get('fecha')
    fecha_hasta = request.form.get('fecha_hasta')

    if id_buscar is None or fecha_hasta is None:
        flash("Faltan campos obligatorios en la busqueda")
        return render_template('prestamo_detalle.html')
    if id_buscar == "" or fecha_hasta == "":
        flash("Sin resultados", "success")
        return redirect (url_for('prestamo'))    
    
    fecha_solicitud = datetime.strptime(id_buscar, '%Y-%m-%d').date()
    fecha_solicitud_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()

    usuario = buscarUsuarios()
    estado = buscarEstados()
    rows = buscarPrestamo(fecha_solicitud, fecha_solicitud_hasta)
    role = session.get('role')
    if rows is None or not rows:
        rows=[]
        flash("Sin resultados", "success")
        return render_template('prestamo_detalle.html')
    return render_template('prestamo_detalle.html', prestamos=rows, usuarios = usuario, estados = estado, roles = role)


@app.route('/buscar', methods= ['POST', 'GET'])
@login_required
def buscar():
    id_buscar = request.form.get('id_buscar')
    if id_buscar is None:
        flash("Faltan campos obligatorios en la solicitud")
        return render_template('subsidio.html')
    if id_buscar == "":
        return redirect (url_for('subsidio'))
    else:
        rows = obtener_datos_subsidio(id_buscar)
        if rows is None:
            rows = []  # Asegúrate de que 'rows' sea una lista vacía en lugar de None
        session['clientes'] = rows
        return render_template('subsidio.html', clientes=rows)


@app.route('/buscarWalton', methods= ['POST', 'GET'])
def buscarWalton():            
    fecha_ini = request.form.get('fecha_formateada')
    nro_auto = request.form.get('nro_auto')

    if fecha_ini is None or nro_auto is None:
        flash("Faltan campos obligatorios en la solicitud")
        return render_template('walton.html')
        
    nro_auto = int(nro_auto)
    rows = obtener_datos_prestamos(fecha_ini)
    resultados = []

    if not rows:
        flash("Sin resultados")
        return render_template('walton.html')
    else:
        for filas in rows:
            cont = 1
            while cont <= 10:
                nro_auto += 1
                resultados.append([filas[0], filas[1], filas[2], filas[3], nro_auto, filas[4], filas[5]])
                cont += 1

    session['autorizaciones'] = resultados
    return render_template('walton.html', autorizaciones=resultados)

    
@login_manager.unauthorized_handler
def manejar_no_autorizado():
    flash('Debes iniciar sesión para acceder a esta página.', 'warning')
    session['next'] = request.url
    return redirect(url_for('login'))

# Función para reiniciar la aplicación
def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)

# Función que se ejecutará al final del día
def end_of_day_job():
    print("Reiniciando la aplicación al final del día.")
    # Detener la instancia actual del servidor Flask
    func = request.environ.get('werkzeug.server.shutdown')
    if func is not None:
        func()
    restart_program()

# Configura la tarea programada para ejecutarse al final del día (puedes ajustar el horario según tus necesidades)
schedule.every().day.at("00:00").do(end_of_day_job)

# Función para ejecutar el planificador en un hilo separado
def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Inicia el hilo del planificador junto con la aplicación Flask
if __name__ == "__main__":
    scheduler_thread = threading.Thread(target=schedule_thread)
    scheduler_thread.start()
    app.run(host='10.10.10.121', port=5000, debug=True)