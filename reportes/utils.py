import datetime
import copy

__author__ = 'German Alzate'


def fechas_reporte_generador(fecha_inicial, fecha_final):
    """
    Generador que a partir de una fecha inicial y otra fecha final, retorna una tupla de fechas
    entre estos dos parametros, con rango de una semana, cumpliendose esta condición hasta que
    se supere la fecha_final

    :rtype tuple:

    :returns:
        Una tupla de fechas a partir de otra, sin que pase de la semana en donde se encuentra la fecha inicial.

    :param fecha_inicial:
        Un objeto del tipo ``datetime.date`` o ``datetime.datetime`` a partir de el cual se empieza a buscar
        la fecha límite para el reporte.

    :param fecha_final:
        Un objeto del tipo ``datetime.date`` o ``datetime.datetime`` el cual es la fecha límite para devolver un
        dia de reporte.
    """
    _fecha_final = copy.deepcopy(fecha_final)
    fecha_inicial -= datetime.timedelta(days=fecha_inicial.isoweekday() - 1)
    fecha_final = fecha_inicial + datetime.timedelta(days=6)  # se agregan 7 dias para que siempre sea lunes.

    while fecha_inicial < _fecha_final:
        yield fecha_inicial, fecha_final
        fecha_inicial += datetime.timedelta(days=7)
        fecha_final += datetime.timedelta(days=7)


def generar_csv(fecha_inicial, fecha_final):
    import csv
    from grupos.models import Grupo, ReunionGAR

    with open('no_hicieron_reunion.csv', 'w') as _file:
        writer = csv.writer(_file)

        for inicio, fin in fechas_reporte_generador(fecha_inicial, fecha_final):
            no_realizadas = ReunionGAR.objects.no_realizadas(inicio, fin)
            grupos = Grupo.objects.annotate_estado(fecha=fin).activos().filter(
                id__in=no_realizadas.values_list('grupo', flat=True)
            ).distinct()
                
            writer.writerow([inicio, fin])
            writer.writerow(['RED', 'CABEZA RED', 'LIDERES'])

            for grupo in grupos:
                writer.writerow([grupo.red, str(grupo.cabeza_red), str(grupo)])
        
        print('terminoooooooooooo')


# from reportes.utils import generar_csv
# fecha_inicial = datetime.date(2018, 1, 1)
# fecha_final = datetime.date(2018, 2, 1)

