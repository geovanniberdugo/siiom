# Python Package
import datetime
import calendar

__author__ = 'German Alzate'


class Dias(object):
    LUNES = 0
    MARTES = 1
    MIERCOLES = 2
    JUEVES = 3
    VIERNES = 4
    SABADO = 5
    DOMINGO = 6


def get_pascua_day(year):
    """
    Algoritmo que devuelve la fecha en la que se celebran las pascuas
    esta fecha es la base de muchos festivos, sacado de:
    https://es.wikipedia.org/wiki/Anexo:Implementaciones_del_algoritmo_de_c%C3%A1lculo_de_la_fecha_de_Pascua#Algoritmo_en_Python
    """
    # Constantes mágicas
    M = 24
    N = 5

    # Cálculo de residuos
    a = year % 19
    b = year % 4
    c = year % 7
    d = (19 * a + M) % 30
    e = (2 * b + 4 * c + 6 * d + N) % 7

    # Decidir entre los 2 casos:
    if d + e < 10:
        dia = d + e + 22
        mes = 3
    else:
        dia = d + e - 9
        mes = 4

    # Excepciones especiales (según artículo)
    if dia == 26 and mes == 4:
        dia = 19
    if dia == 25 and mes == 4 and d == 28 and e == 6 and a > 10:
        dia = 18

    return datetime.date(year=year, day=dia, month=mes)


def get_fechas_dias_fijos(year):
    """
    Funcion que devuelve las fechas que son de dias fijos
    """
    # Se usa una tupla con (dia, mes) y se arman las fechas con el año a partir de los args
    DIAS_MESES_FIJOS = (
        (1, 1),  # Dia, Mes (Año nuevo)
        (7, 8),  # Batalla Boyaca
        (1, 5),  # Dia Trabajo
        (20, 7),  # Grito Independencia
        (8, 12),  # Inmaculada Concepción
        (25, 12),  # Navidad
    )

    _LIST = []

    for dia, mes in DIAS_MESES_FIJOS:
        _LIST.append(datetime.date(year=year, day=dia, month=mes))

    return _LIST


def get_fechas_primer_lunes(year):
    """
    Devuelve una lista con las fechas de festivos por primer lunes de acuerdo a una fecha
    base
    """
    DIAS_MESES_BASE = (
        (15, 8),  # Dia, Mes (Asuncion de la Virgen)
        (12, 10),  # Dia de la raza
        (6, 1),  # Epifanía (Reyes Magos)
        (11, 11),  # Independencia de Cartagena
        (19, 3),  # San José
        (29, 6),  # San Pedro y San Pablo
        (1, 11),  # Todos los Santos
    )

    _LIST = []

    for dia, mes in DIAS_MESES_BASE:
        fecha = datetime.date(day=dia, month=mes, year=year)
        dia_semana = calendar.weekday(fecha.year, fecha.month, fecha.day)
        if dia_semana != Dias.LUNES:
            while dia_semana != Dias.LUNES:
                fecha += datetime.timedelta(days=1)
                dia_semana = calendar.weekday(fecha.year, fecha.month, fecha.day)
        _LIST.append(fecha)

    return _LIST


def get_fechas_respecto_pascua(year):
    """
    Retorna las fechas con respecto a los dias de pascua, ya sea sumando o restando dias
    """
    DIAS_BASES = (
        (-7),  # Domingo de Ramos
        (-3),  # Jueves Santo
        (-2),  # Viernes Santo
        (43),  # Asencion de Jesus
        (64),  # Corpus Christi
        (71),  # Sagrado Corazon de Jesus
    )

    _LIST = []

    for dias in DIAS_BASES:
        pascua = get_pascua_day(year)
        _LIST.append(pascua + datetime.timedelta(days=dias))

    return _LIST


def get_festivos(year, exclude_dates=[], added_dates=[]):
    """
    Devuelve la lista de todos los festivos en un año determinado
    """

    pascua = get_pascua_day(year)
    festivos_pascua = get_fechas_respecto_pascua(year)
    festivos_lunes = get_fechas_primer_lunes(year)
    festivos_fijos = get_fechas_dias_fijos(year)

    _festivos = [pascua]

    _festivos.extend(festivos_pascua)
    _festivos.extend(festivos_lunes)
    _festivos.extend(festivos_fijos)

    return list((set(_festivos) ^ set(exclude_dates)) | set(added_dates))
