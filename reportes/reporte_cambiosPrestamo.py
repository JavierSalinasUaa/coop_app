from flask import Blueprint, session, make_response
from models.reporte import generate_pdf_cambios

# Crear un objeto Blueprint
reporteCamb = Blueprint('reporteCamb', __name__)

@reporteCamb.route('/reporteCamb', methods=['GET'])
def reporteCambios():
    # Data for the table (replace this with your actual data)
    titulo = "Reporte de Cambios de Prestamos"
    filas = session['prestamos']
    data = [
    ["Nro de Prestamo", "Estado anterior", "Estado Actual", "Solicitado Por", "Fecha Modificacion", "Usuario Modificador"]
    ]

    for row in filas:
        try:
            data.append([str(row[1]), row[7], row[8], row[2], row[5], str(row[6])])

        except Exception as e:
            print(f"Error al procesar la fila {row}: {e}")

    # Ahora 'data' contiene todas las filas
    response = make_response(generate_pdf_cambios(data, titulo))
    response.headers['Content-Disposition'] = 'filename=report.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response