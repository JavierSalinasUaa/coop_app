from datetime import datetime
from flask import Blueprint, session, make_response
from reporte import generate_pdf

# Crear un objeto Blueprint
reporteFiltro = Blueprint('reporteFiltro', __name__)

@reporteFiltro.route('/reporteFiltro', methods=['GET'])
def reporteFiltros():
    # Data for the table (replace this with your actual data)
    titulo = "Filtros de Prestamos"
    filas = session['prestamos_por_fecha']
    array_ordenado = dict(sorted(filas.items(), key=lambda item: datetime.strptime(item[0], "%Y-%m-%d %H:%M:%S")))

    # Ahora 'data' contiene todas las filas
    response = make_response(generate_pdf(array_ordenado, titulo))
    response.headers['Content-Disposition'] = 'filename=report.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response