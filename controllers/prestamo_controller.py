from datetime import datetime
import traceback
from flask import Blueprint, app, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from utils.logger import logger

from models.mysql_config import buscarEstados, buscarPrestamo, eliminarPrestamo, guardarPrestamo, updatePrestamo, ver_historial_prestamo, verificar_existencia
from models.source_prestamo import buscarUsuarios, obtener_datos_solicitud_prestamo
from utils.decorators import role_required

routes_prestamo = Blueprint('routes_prestamo', __name__)

@routes_prestamo.route('/prestamo_detalle')
@role_required({'ARCHIVO', 'ADMINISTRADOR', 'CREDITO'})
def prestamo():
    try:
        session['prestamos'] = ''
        session['prestamos_por_fecha'] = {}
        rows = buscarEstados()
        filas = buscarUsuarios()
        rol_usuario = session.get('role')
        # Pasar los datos de `estado` a la plantilla
        return render_template('prestamo_detalle.html', estados=rows, usuarios=filas, roles = rol_usuario)
    except Exception as e:
        logger.error(f"Error en /prestamo_detalle: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "Ocurrió un error en la página", 500
    
@routes_prestamo.route('/guardarPrestamos', methods=['POST'])
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

@routes_prestamo.route('/guardarPre', methods=['POST'])
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


@routes_prestamo.route('/borrarPre', methods=['GET', 'POST'])
def borrarPre():
    if request.method == 'POST':
        nro_prestamo = request.form['nro_prestamo']
    row = eliminarPrestamo(nro_prestamo)

    if row:
        flash("Préstamo eliminado exitosamente.", "success")
        return jsonify({"status": "success", "redirect_url": url_for('routes_prestamo.prestamo')})
    else:
        return jsonify({"status": "error", "message": "No se pudo eliminar el préstamo."})

@routes_prestamo.route('/historialPre', methods=['GET', 'POST'])
def historialPre():
    if request.method == 'POST':
        nro_prestamo = request.form['nro_prestamo']
    row = ver_historial_prestamo(nro_prestamo)

    if row:
        session['prestamos'] = row
        return jsonify({"status": "success", "redirect_url": url_for('reporteCamb.reporteCambios')})
    else:
        return jsonify({"status": "error", "message": "No se encontraron cambios."})
    
@routes_prestamo.route('/filtrosPre', methods=['GET', 'POST'])
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

@routes_prestamo.route('/buscarPrestamo', methods=['POST'])
def buscar_datos():
        # Validar si 'fecha_solicitud' está presente
        fecha_solicitud = request.form.get('fecha_solicitud')
        fecha_solicitud_fin = request.form.get('fecha_solicitud_fin')
        if fecha_solicitud is None or fecha_solicitud_fin is None:
            return jsonify({"error": "La fecha de solicitud es obligatoria"}), 400
        
        if not fecha_solicitud or not fecha_solicitud_fin:
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

@routes_prestamo.route('/buscarPre', methods= ['POST', 'GET'])
@login_required
def buscarPre():
    id_buscar = request.form.get('fecha')
    fecha_hasta = request.form.get('fecha_hasta')

    if id_buscar is None:
        flash("Faltan campos obligatorios en la busqueda", "success")
        return render_template('prestamo_detalle.html')
    if id_buscar == "" or fecha_hasta == "":
        flash("Sin resultados", "success")
        return redirect (url_for('routes_prestamo.prestamo'))    
    
    fecha_solicitud = datetime.strptime(id_buscar, '%Y-%m-%d').date()
    fecha_solicitud_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()

    usuario = buscarUsuarios()
    estado = buscarEstados()
    rows = buscarPrestamo(fecha_solicitud, fecha_solicitud_hasta)
    role = session.get('role')
    if rows is None or not rows:
        rows=[]
        flash("Sin resultados", "success")
        return redirect (url_for('routes_prestamo.prestamo')) 
    return render_template('prestamo_detalle.html', prestamos=rows, usuarios = usuario, estados = estado, roles = role)