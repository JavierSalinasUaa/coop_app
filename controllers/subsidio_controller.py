from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import login_required

from models.source_subsidio import obtener_datos_subsidio

routes_subsidio = Blueprint('routes', __name__)

@routes_subsidio.route('/buscar', methods= ['POST', 'GET'])
@login_required
def buscar():
    id_buscar = request.form.get('id_buscar')
    if id_buscar is None:
        flash("Faltan campos obligatorios en la solicitud")
        return render_template('subsidio.html')
    if id_buscar == "":
        return redirect (url_for('routes.subsidio'))
    else:
        rows = obtener_datos_subsidio(id_buscar)
        if rows is None:
            rows = []  # Asegúrate de que 'rows' sea una lista vacía en lugar de None
        session['clientes'] = rows
        return render_template('subsidio.html', clientes=rows)
    
@routes_subsidio.route('/subsidio')
@login_required
def subsidio():
    session['clientes'] = ''
    return render_template('subsidio.html')