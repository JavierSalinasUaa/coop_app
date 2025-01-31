from flask import Flask, jsonify, render_template, request, redirect, session, url_for, flash
from flask_login import LoginManager, current_user, login_required, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from datetime import datetime, timedelta
from utils.logger import logger
from controllers.subsidio_controller import routes_subsidio
from controllers.walton_controller import routes_walton
from controllers.prestamo_controller import routes_prestamo
from models.ldap import obtenerdatos
from models.entities.User import Usuario
from reportes.reporte_subsidio import report
from reportes.reporte_walton import reporte
from reportes.reporte_cambiosPrestamo import reporteCamb
from reportes.reporte_filtros import reporteFiltro
import schedule
import time
import os
import sys
import threading

app = Flask(__name__)


app.secret_key = 'B!1w8NAt1T^%kvhUI*S^'
app.config['SESSION_TYPE'] = 'filesystem'

app.register_blueprint(report, url_prefix='/reporte')
app.register_blueprint(reporte, url_prefix='/reporteWalton')
app.register_blueprint(reporteCamb, url_prefix='/reporteCamb')
app.register_blueprint(reporteFiltro, url_prefix='/reporteFiltros')
app.register_blueprint(routes_subsidio, url_prefix='/routes')
app.register_blueprint(routes_walton, url_prefix='/routes_walton')
app.register_blueprint(routes_prestamo, url_prefix='/routes_prestamo')

csrf = CSRFProtect()

login_manager = LoginManager(app)
login_manager.login_view = 'login'
Session(app)

TIEMPO_INACTIVIDAD_SEGUNDOS = 900  # 15 minutos

# Decorador para capturar eventos antes de la solicitud
@app.before_request
def log_before_request():
    app.logger.info('%s', request.path)

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

            # 🛑 Aquí cambiaremos el comportamiento según si es AJAX o no
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": "Usuario no autenticado por inactividad"}), 401  # 🔹 En AJAX, devuelve JSON
            else:
                return redirect(url_for('login'))  # 🔹 En peticiones normales, sigue redirigiendo

    session['ultima_actividad'] = datetime.utcnow()

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


@login_manager.user_loader
def cargar_usuario(user_id):
    # Implementa la lógica para cargar el usuario desde tu sistema
    return Usuario(user_id, user_id)

@app.route('/login_dom', methods=['GET', 'POST'])
def login_dom():
    urls = ["buscarPre", "filtrosPre", "borrarPre"]
    if request.method == 'POST':
        user = request.form['usuario']
        passw = request.form['contrasena']

        data = obtenerdatos(user, passw)
        if data:
            next_url = session.get('next')
            if next_url:
                if any(fragmento in next_url for fragmento in urls):
                #if next_url in urls:                    
                    return redirect (url_for('routes_prestamo.prestamo'))
                session.pop('next')  # Eliminate the next URL from the session
                return redirect(next_url)
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrecto")
            return render_template('login_domain.html')
        

@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/logout')
def cerrar_sesion():
        logout_user()
        session.clear()
        flash('Has cerrado sesión exitosamente.')
        return redirect(url_for('login'))
    
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
    app.config['DEBUG'] = True
    app.run(host='0.0.0.0', port=5000, debug=True)
