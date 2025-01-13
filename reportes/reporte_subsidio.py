from flask import Blueprint, session, make_response
from reporte import generate_pdf

# Crear un objeto Blueprint
report = Blueprint('reporte', __name__)

@report.route('/reporte', methods=['GET'])
def reporte():
    # Data for the table (replace this with your actual data)
    titulo = "Reporte de Consultas"
    filas = session['clientes']
    data = [
    ["Nro Socio", "Nro Solicitud", "Fecha de Solicitud", "Tipo Subsidio", "Nombre"]
    ]

    for row in filas:
        data.append([str(row[0]), row[1], row[2].strftime('%Y-%m-%d'), row[3], row[4]])

    # Ahora 'data' contiene todas las filas
    response = make_response(generate_pdf(data, titulo))
    response.headers['Content-Disposition'] = 'filename=report.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response