from io import BytesIO
import xlsxwriter
import collections
import datetime


class Excel(object):

    START_ROW = 0
    START_COL = 1
    _LETTERS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    def __init__(self, file=BytesIO()):
        self._buffer = file
        self.row = self.col = 0
        self._pages = collections.OrderedDict()
        self.workbook = xlsxwriter.Workbook(self._buffer)

    def read(self):
        """
        Funcion que crea un documento de excel.
        """
        self.close()
        return self._buffer.getvalue()

    def close(self):
        """
        Metodo que cierra el documento de excel.
        """
        # Metodo que intenta cerrar el libro
        try:
            return self.workbook.close()
        except TypeError:
            return self.workbook.close()
        finally:
            pass

    def _add_sheet(self, name):
        """Agrega una pagina al workbook."""

        pages = [x for x in self._pages if x.startswith(name)]

        if len(pages) == 0:
            self._pages[name] = self.workbook.add_worksheet(name)
            self._pages[name].set_default_row(hide_unused_rows=True)
        return self._pages[name]

    def get_sheet(self, title=''):
        """Retorna la hoja de trabajo actual Y/O Asigna una."""

        if not title and not self._actual_sheet:
            if not len(self._pages):
                self._actual_sheet = self._add_sheet('Page 1')
            else:
                for page in self._pages:
                    self._actual_sheet = self._pages[page]
                    break
        elif not title and self._actual_sheet:
            self._actual_sheet = self._actual_sheet
        else:
            if title not in self._pages:
                raise IndexError(
                    'Pagina "%s"" no está entre las paginas "%s"' % (title, ', '.join([x for x in self._pages]))
                )
            self._actual_sheet = self._pages[title]
        return self._actual_sheet

    def normalize_fields(self, col=True, row=True):
        """Metodo para volver a la ultima fila y columna a su posicion inicial"""

        if isinstance(col, int) and not isinstance(col, bool):
            self.col = col
        else:
            if col is True:
                self.col = self.START_COL
        if isinstance(row, int) and not isinstance(row, bool):
            self.row = row
        else:
            if row is True:
                self.row = self.START_ROW

        if self.row is True or self.col is True:
            raise ValueError("self.last_row is: %d and self.last_col is: %d" % (self.row, self.col))

    def write_line(self, text, **kwargs):
        """
        Metodo para escribir de acuerdo a posicion en fila/columna.
        """

        style = kwargs.pop('style', None) or self.style_body

        row = kwargs.pop('row', None) or self.row
        col = kwargs.pop('col', None) or self.col

        length = kwargs.pop('length', None)

        sheet = self.get_sheet()
        to_python = self.format_data(text)
        sheet.write(row, col, to_python, style)

        if isinstance(to_python, str):
            if length is not None and 10 + len(to_python) > length:
                length = 10 + len(to_python)
            else:
                length = length or (10 + len(to_python))
        else:
            if length is not None and 2 * 6 > length:
                length = 2 * 6
            else:
                length = length or (2 * 6)

        sheet.set_column('{0}:{0}'.format(self.get_letter_by_index(col)), length)
        return length

    def get_letter_by_index(self, indx):
        sufix = ''
        while indx > len(self._LETTERS) - 1:
            indx = indx - len(self._LETTERS)
            if not sufix:
                sufix = 0
            sufix += 1
        return '{}{}'.format(self._LETTERS[indx], sufix)

    @staticmethod
    def format_data(value):
        """Funcion statica para formatear los datos, con un orden"""

        if value is None:
            return ''
        if isinstance(value, str):
            return value.upper()
        elif isinstance(value, int):
            return value
        elif isinstance(value, float):
            return float("%.2f" % value)
        elif isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d')
        elif callable(value):
            return value()
        try:
            return value.__str__()
        except:
            raise ValueError('DataType found not expected "%s"' % value.__class__.__name__)

    @property
    def style_title(self):
        return self.workbook.add_format({
            'bold': True,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

    @property
    def style_header(self):
        return self.workbook.add_format({
            'bg_color': '#F0F0F0',
            'color': 'black',
            'align': 'center',
            'valign': 'top',
            'border': 1,
            'font_size': 10.5
        })

    @property
    def style_body(self):
        return self.workbook.add_format({
            'bg_color': '#F7F7F7',
            'color': 'black',
            'align': 'center',
            'valign': 'top',
            'border': 1,
            'italic': True,
            'font_size': 10.5
        })


class ReporteInstituto(Excel):

    def __init__(self, data, materias, *args, **kwargs):
        self.data = data
        self.materias = materias
        super().__init__(*args, **kwargs)
        titulo = 'Page 1'
        self._render_reporte()

    def _getattr(self, obj, value):
        """
        Funcion que retorna el atributo deseado, y de no ser encontrado el atributo, retorna
        el atributo como parametro que fue buscado
        """
        _attrs = value.split('.')
        for attr in _attrs:
            val = getattr(obj, attr.strip(), False)
            if val is False:
                break
            obj = val
        if val is False:
            return ''
        return self.format_data(val)

    def getattr(self, obj, value):
        attrs = value.split(',')
        result = []
        for attr in attrs:
            result.append(self._getattr(obj, attr.strip()))
        return ' '.join(result) 

    def _render_reporte(self):
        self._actual_sheet = self._add_sheet('Base Datos')

        titles = [
            ('NOMBRE', 'nombre,primer_apellido,segundo_apellido'),
            ('CEDULA', 'cedula'), ('RED', 'grupo.red'),
            ('SUBRED', 'grupo.cabeza_red'),
        ] + [(x.nombre, 'estudiante.nota_materia_{}'.format(x.id)) for x in self.materias]

        length = 0

        start_filter = (self.row, self.col, )
        end_filter = None

        for title in titles:
            self.write_line(title[0], style=self.style_title)
            self.row += 1

            for data in self.data:
                possible_length = self.write_line(
                    self.getattr(data, title[1]), style=self.style_body, length=length
                )
                if possible_length > length:
                    length = possible_length
                self.row += 1
            length = 0
            end_filter = (self.row, self.col, )
            self.normalize_fields(col=self.col + 1)

        self._actual_sheet.autofilter(*start_filter + end_filter)
