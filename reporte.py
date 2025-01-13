from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import LEGAL
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
import io

def generate_pdf_cambios(data, titulo):
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=LEGAL)

    # Set title
    pdf.title = titulo

    # Obtener el ancho de la página y dejar un margen
    ancho_pagina, altura_pagina = LEGAL
    margen = 0.5 * inch
    ancho_disponible = ancho_pagina - 2 * margen

    # Calcular el ancho de cada columna
    num_columnas = len(data[0])
    ancho_columna = ancho_disponible / num_columnas

    # Crear tabla y estilo
    table_data = []
    for row in data:
        table_data.append([Paragraph(str(cell), getSampleStyleSheet()['BodyText']) for cell in row])


    table = Table(table_data, colWidths=[ancho_columna] * num_columnas)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), (0.8, 0.8, 0.8)),  # Header background color
        ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),         # Header text color
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),             # Center alignment for all cells
        ('INNERGRID', (0, 0), (-1, -1), 0.25, (0, 0, 0)),  # Inner grid color and width
        ('BOX', (0, 0), (-1, -1), 0.25, (0, 0, 0))        # Border color and width
    ])

    table.setStyle(style)

    # Aplicar envoltura de palabras a todas las celdas
    for i in range(len(data)):
        for j in range(len(data[i])):
            table.setStyle(TableStyle([('WORDWRAP', (j, i), (j, i))]))

    # Añadir título
    styles = getSampleStyleSheet()
    title = titulo
    title_style = styles['Title']
    title_para = Paragraph(title, title_style)

    # Construir PDF
    elements = [title_para, table]

    pdf.build(elements)
    buffer.seek(0)
    return buffer.getvalue()  # Devolver el contenido del PDF como 

def generate_pdf(data, titulo):
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=LEGAL)

    # Configuración de estilos
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    section_title_style = styles['Heading2']
    body_style = styles['BodyText']
    body_style.fontSize = 10  # Reducir tamaño de fuente
    body_style.leading = 10  # Reducir interlineado

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),      # Color de fondo del encabezado
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Color del texto del encabezado
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),             # Alineación centrada
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black), # Líneas internas
        ('BOX', (0, 0), (-1, -1), 0.25, colors.black),     # Borde exterior
        ('WORDWRAP', (0, 0), (-1, -1)),                   # Permitir envoltura de texto
    ])

    # Calcular ancho dinámico para la columna de titulares
    max_titular_width = 0
    for prestamos in data.values():
        for prestamo in prestamos:
            titular = prestamo.get("titular", "")
            # Calcular el ancho del texto en puntos
            titular_width = stringWidth(titular, body_style.fontName, body_style.fontSize)
            max_titular_width = max(max_titular_width, titular_width)

    # Convertir el ancho máximo a pulgadas y agregar un margen
    titular_col_width = max(2 * inch, max_titular_width / 72 + 0.2)

    # Crear el contenido del PDF
    elements = [Paragraph(titulo, title_style), Spacer(1, 0.2 * inch)]

    for fecha, prestamos in data.items():
        # Título de la sección (fecha)
        # Formato de la fecha en la cadena
        formato = "%Y-%m-%d %H:%M:%S"

        # Convertir la cadena a datetime usando strptime
        fecha_objeto = datetime.strptime(fecha, formato)
        fecha_solo_ymd = fecha_objeto.strftime("%Y-%m-%d")
        elements.append(Paragraph(f"Fecha: {fecha_solo_ymd}", section_title_style))
        elements.append(Spacer(1, 0.1 * inch))

        # Crear tabla para los datos de la fecha
        encabezados = ["Nro Préstamo", "Titular", "Importe Préstamo", "Encargado"]
        filas = [
            [
                Paragraph(prestamo.get("nro_prestamo", ""), body_style),
                Paragraph(prestamo.get("titular", ""), body_style),
                prestamo.get("importe_prestamo", ""),
                Paragraph(prestamo.get("encargado", ""), body_style),
            ]
            for prestamo in prestamos
        ]
        table_data = [encabezados] + filas

        # Anchos dinámicos de columna
        col_widths = [1.5 * inch, titular_col_width, 1.5 * inch, 1.5 * inch]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(table_style)

        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))  # Espaciado entre secciones

    # Construir el PDF
    pdf.build(elements)
    buffer.seek(0)
    return buffer.getvalue()  # Devolver el contenido del PDF como bytes