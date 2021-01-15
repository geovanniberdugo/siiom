import os
import glob
import logging
from contextlib import suppress
from wand.image import Image

CARPETA_PDF_TO_IMAGE = '/pdf2img/'
logger = logging.getLogger('siiom.{}'.format(__name__))

def get_route(archivo):
    """
    Devuelve la ruta completa de un archivo hasta el directorio que compone el archivo
    """

    if os.path.exists(archivo.path):

        ruta = '/'
        _rutas = archivo.path.split('/')

        while ruta == '/':
            if os.path.isdir(ruta.join(_rutas)):
                ruta = ruta.join(_rutas)
            else:
                del _rutas[len(_rutas) - 1]

        return ruta
    return None


def get_filenames(archivo):
    """
    Devuelve una lista con las imagenes pertenecientes a un solo archivo pdf
    """
    global CARPETA_PDF_TO_IMAGE
    file_especifications = archivo.name.split('/')
    file_name = file_especifications[len(file_especifications) - 1]
    ruta = get_route(archivo)
    try:
        os.chdir('{}{}'.format(ruta, CARPETA_PDF_TO_IMAGE))
        return glob.glob(file_name.split('.')[0] + '*')
    except FileNotFoundError:
        logger.exception("Archivo no encontrado para la ruta %s.", archivo.url)
        return []


def pdf_to_png(archivo, extencion='jpg', _ruta=False, save=False):
    """
    Funcion que se encarga de pasar los archivos de pdf en png y agruparlos en carpetas
    """
    global CARPETA_PDF_TO_IMAGE
    __accepted__ = ['png', 'jpg', 'JPEG', 'gif', 'IMAGE', 'PNJ', 'ico', 'jpeg', 'bmp', 'BMP']

    if len(extencion.split('.')) > 1:
        extencion = extencion.split('.')[len(extencion) - 1]

    if os.path.exists(archivo.path):

        file_especifications = archivo.name.split('/')
        # area = file_especifications[1]
        # registro = file_especifications[2]
        file_name = file_especifications[len(file_especifications) - 1]

        ruta = get_route(archivo)

        if save:
            if file_name.split('.')[len(file_name.split('.')) - 1] not in __accepted__:
                imagen = Image(filename=archivo.path)
                if not os.path.exists(ruta + CARPETA_PDF_TO_IMAGE):
                    os.mkdir(ruta + CARPETA_PDF_TO_IMAGE)
                    if not os.path.exists(ruta + CARPETA_PDF_TO_IMAGE):
                        raise TypeError("Directory was not created yet")
                imagen.save(filename=ruta + CARPETA_PDF_TO_IMAGE + file_name.split('.')[0] + '.' + extencion)

        if _ruta:
            _return_ruta = ruta + CARPETA_PDF_TO_IMAGE
            return _return_ruta
        os.chdir('{}{}'.format(ruta, CARPETA_PDF_TO_IMAGE))
        return ruta + CARPETA_PDF_TO_IMAGE  # , glob.glob(file_name.split('.')[0] + '*')

    return None


def get_media_url(path):
    """
    Devuelve la url del archivo
    """
    media_path = path.split('/')
    p = '/'
    while p == '/':
        if os.path.isfile(p.join(media_path)):
            MEDIA_URL = 'media'
            del media_path[0: media_path.index(MEDIA_URL)]
            p = p.join(media_path)
        else:
            del media_path[len(media_path) - 1]
    return '/' + p
