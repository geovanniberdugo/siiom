# -*- coding: utf-8 -*-

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend, LineLegend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer


__author__ = 'Tania'


color_list = [
    colors.red, colors.yellow, colors.green, colors.blue, colors.cyan, colors.magenta,
    colors.orange, colors.lime, colors.turquoise, colors.azure, colors.violet, colors.crimson,
    colors.orangered, colors.chartreuse, colors.aquamarine, colors.skyblue, colors.indigo, colors.lavender,
    colors.gold, colors.greenyellow, colors.powderblue, colors.purple
]


class BarChart(Drawing):

    def __init__(self, width=400, height=200, data=[], labels=[], legends=[], *args, **kw):
        Drawing.__init__(self, width, height, *args, **kw)
        self.add(VerticalBarChart(), name='chart')
        self.add(Legend(), name='legend')

        self.chart.x = 15
        self.chart.y = 15
        self.chart.width = self.width - 20
        self.chart.height = self.height - 40
        self.chart.data = data

        self.chart.categoryAxis.categoryNames = labels
        self.chart.categoryAxis.labels.boxAnchor = 'ne'
        self.chart.categoryAxis.labels.angle = 30

        for i in range(len(data)):
            self.chart.bars[i].fillColor = color_list[i]

        self.legend.alignment = 'right'
        self.legend.x = self.width
        self.legend.y = self.height - self.height / 4
        self.legend.dx = 8
        self.legend.dy = 8
        self.legend.deltay = 10
        self.legend.dxTextSpace = 3
        self.legend.columnMaximum = 10
        self.legend.colorNamePairs = [(color_list[i], legends[i]) for i in range(len(legends))]


class PieChart(Drawing):

    def __init__(self, width=400, height=200, data=[], labels=[], legends=[], *args, **kw):
        Drawing.__init__(self, width, height, *args, **kw)
        self.add(Pie(), name='chart')
        self.add(Legend(), name='legend')

        self.chart.x = self.width / 4
        self.chart.y = 15
        self.chart.width = self.width - 150
        self.chart.height = self.height - 40
        self.chart.data = data

        for i in range(len(data)):
            self.chart.slices[i].fillColor = color_list[i]

        self.legend.alignment = 'right'
        self.legend.x = self.width - 20
        self.legend.y = self.height - self.height / 4
        self.legend.dx = 8
        self.legend.dy = 8
        self.legend.deltay = 10
        self.legend.dxTextSpace = 3
        self.legend.columnMaximum = 10
        self.legend.colorNamePairs = [(color_list[i], legends[i]) for i in range(len(legends))]


class LineChart(Drawing):

    def __init__(self, width=400, height=200, data=[], labels=[], legends=[], *args, **kw):
        Drawing.__init__(self, width, height, *args, **kw)
        self.add(HorizontalLineChart(), name='chart')
        self.add(LineLegend(), name='legend')

        self.chart.x = 15
        self.chart.y = 15
        self.chart.width = self.width - 20
        self.chart.height = self.height - 40
        self.chart.data = data

        self.chart.categoryAxis.categoryNames = labels
        self.chart.categoryAxis.labels.angle = 45

        for i in range(len(data)):
            self.chart.lines[i].strokeColor = color_list[i]

        self.legend.alignment = 'right'
        self.legend.x = self.width
        self.legend.y = self.height - self.height / 4
        self.legend.dx = 8
        self.legend.dy = 1
        self.legend.deltay = 10
        self.legend.dxTextSpace = 3
        self.legend.columnMaximum = 10
        self.legend.colorNamePairs = [(color_list[i], legends[i]) for i in range(len(legends))]


class PdfTemplate(SimpleDocTemplate):

    def __init__(self, filename, titulo, opciones, datos, tipo, total=False, tabla=None, **kw):
        SimpleDocTemplate.__init__(self, filename, pagesize=letter, **kw)

        # Estilos
        style = getSampleStyleSheet()

        # Titulo
        header = Paragraph(titulo, style['Title'])

        # Opciones
        op = ''
        if 'fi' in opciones:
            op = op + '<b>Fecha Inicial:</b> %s<br />' % opciones['fi']
        if 'ff' in opciones:
            op = op + '<b>Fecha Final:</b> %s<br />' % opciones['ff']
        if 'g' in opciones:
            op = op + '<b>Grupo:</b> %s<br />' % opciones['g']
        if 'gi' in opciones:
            op = op + '<b>Grupo Inicial:</b> %s<br />' % opciones['gi']
        if 'gf' in opciones:
            op = op + '<b>Grupo Final:</b> %s<br />' % opciones['gf']
        if 'opt' in opciones:
            op = op + '<b>Opcion:</b> %s<br />' % opciones['opt']
        if 'ano' in opciones:
            op = op + '<b>Año:</b> %s<br />' % opciones['ano']
        if 'red' in opciones:
            op = op + '<b>Red:</b> %s<br />' % opciones['red']
        if 'predica' in opciones:
            op = op + '<b>Predica:</b> %s<br />' % opciones['predica']
        if 'total_grupos' in opciones:
            op = op + '<b>Total de grupos:</b> %s<br />' % opciones['total_grupos']
        if 'total_grupos_inactivos' in opciones:
            op = op + '<b>Total de grupos inactivos:</b> %s<br />' % opciones['total_grupos_inactivos']
        op_p = Paragraph(op, style['Normal'])

        # Tabla

        if tabla is not None:
            d = tabla
            f = 7
        else:
            d = datos
            f = 10

        table = Table(d)
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), f),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
        ]

        if total:
            table_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.orange))
        table.setStyle(TableStyle(table_style))

        # Graficos

        sw = True
        if total:
            datos.pop()

        other_labels = datos.pop(0)
        other_labels.pop(0)
        chart_datos = list(zip(*datos))
        labels = list(chart_datos.pop(0))
        if tipo == 1:  # Pie chart
            data = list(chart_datos.pop())
            if sum(data) != 0:
                chart = PieChart(data=data, labels=labels, legends=labels)
            else:
                sw = False
        elif tipo == 2:  # Bar chart
            data = chart_datos
            chart = BarChart(data=data, labels=labels, legends=other_labels)
        else:  # Line chart
            data = chart_datos
            chart = LineChart(data=data, labels=labels, legends=other_labels)

        # Agregar al pdf
        catalog = []
        catalog.append(header)
        catalog.append(Spacer(1, 50))
        catalog.append(op_p)
        catalog.append(Spacer(1, 50))
        catalog.append(table)
        catalog.append(Spacer(1, 60))
        if sw:
            catalog.append(chart)

        self.build(catalog)


class PdfReport(SimpleDocTemplate):

    def __init__(self, filename, titulo, opciones, datos, tipo, total=False, tabla=None, **kw):
        super(PdfReport, self).__init__(filename, pagesize=letter, **kw)

        # Estilos
        style = getSampleStyleSheet()

        # Titulo
        header = Paragraph(titulo, style['Title'])

        # Opciones
        _opciones = ''
        xml_b = '<b>%(title)s:</b> %(value)s<br />'

        for title, value in opciones.items():
            _opciones += xml_b % {
                'title': self.__class__.get_string_options(title),
                'value': value
            }

        opciones_paragraph = Paragraph(_opciones, style['Normal'])

        if tabla is not None:
            f = 7
        else:
            tabla = datos
            f = 10

        table = Table(tabla)

        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), f),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black)
        ]

        if total:
            table_style.append(('BACKGROUND', (0, -1), (-1, -1), colors.orange))
        table.setStyle(TableStyle(table_style))

        # Graficos
        sw = True
        if total:
            datos.pop()
        other_labels = datos.pop(0)
        other_labels.pop(0)
        chart_datos = list(zip(*datos))
        labels = list(chart_datos.pop(0))
        if tipo == 1:  # Pie chart
            data = list(chart_datos.pop())
            if sum(data) != 0:
                chart = PieChart(data=data, labels=labels, legends=labels)
            else:
                sw = False
        elif tipo == 2:  # Bar chart
            data = chart_datos
            chart = BarChart(data=data, labels=labels, legends=other_labels)
        else:  # Line chart
            data = chart_datos
            chart = LineChart(data=data, labels=labels, legends=other_labels)

        # Agregar al pdf
        catalog = []
        catalog.append(header)
        catalog.append(Spacer(1, 50))
        catalog.append(opciones_paragraph)
        catalog.append(Spacer(1, 50))
        catalog.append(table)
        catalog.append(Spacer(1, 60))
        if sw:
            catalog.append(chart)

        self.build(catalog)

    @staticmethod
    def get_string_options(value):
        """
        Retorna el valor de el string dado, cambiando el '_' por un espacio ' '
        """
        SPACE = ' '
        UNDERSCORE = '_'
        if not isinstance(value, str):
            try:
                value = str(value)
            except:
                raise TypeError("Expected String, but found '%s'." % value.__class__.__name__)
        return value.replace(UNDERSCORE, SPACE).title()
