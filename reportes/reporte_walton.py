from flask import Blueprint, session, make_response
import pandas as pd
import io

# Crear un objeto Blueprint
reporte = Blueprint('reporteWalton', __name__)

@reporte.route('/reporteWalton', methods=['GET'])
def reporte_excel():
    # Crear un DataFrame de ejemplo
    filas = session['autorizaciones']
    data = []

    for row in filas:
        data.append(
            {
            "Nro Ci": int(row[0]),
            "Nombre": row[1],
            "Nro Socio": int(row[2]),
            "Nro de Prestamo": int(row[3]),
            "Nro de Autorizacion": row[4],
            "Monto Cuota": float(row[5])
        })
    df = pd.DataFrame(data)

    # Guardar el DataFrame en un archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    output.seek(0)

    # Enviar el archivo Excel como respuesta
    response = make_response(output.read())
    response.headers['Content-Disposition'] = 'attachment; filename=reporte.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    return response