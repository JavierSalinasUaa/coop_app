from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_required

from models.source_walton import obtener_datos_prestamos

routes_walton = Blueprint('routes_walton', __name__)

@routes_walton.route('/walton')
@login_required
def walton():
    return render_template('walton.html')

@routes_walton.route('/buscarWalton', methods= ['POST', 'GET'])
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