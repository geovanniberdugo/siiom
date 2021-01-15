"""

    Update Sábado 13 Agosto 2016

    Hecho por: Ingeniarte Soft


    Datos importantes a tener en cuenta:

        - Para la fecha, el numero maximo de pasos que puede tener una requisicion será de
        7, sin contar que puede tener mas historiales que pasos y el numero minimo
        de pasos para que una requisicion sea finalizada y aprobada será de 5
        dada las condiciones establecidas

        - Cada requisicion contara con un porcentaje de progreso el cual va de acuerdo a la
        posicion donde se encuetre esa requisicion, y el estado de cada detalle de dicha
        requisicion (ITEMS)

        - Para saber donde está cada detalle de la requisicion, se mira la posicion de la
        requisicion a la que pertenece, la posible cantidad de pasos que tendra de acuerdo a
        sus valores, y si ya está pagada o no, la cual le dara un valor de el 100 porciento,
        sabiendo que cada detalle de la requisicion tendrá un valor total de 1 = 100%,
        y en la requisicion para saber su progreso seria el valor en porcentaje de cada detalle
        de la requisicion entre el numero de items o detalles de requisicion que tiene la requisicion
        por 100, dicho de otro modo, la sumatoria de los porcentajes de cada detalle de la requisicion:

        a = 3 (cantidad de items)

        b = [x.valor_porcentaje for x in a]

        c = 0 (no puede ser mayor que a)

        for x in b:
            c += x

        progreso = c / a


        - Para saber el progreso de un detalle de requisicion se procede de la siguiente manera:

        max = 1 (valor maximo que puede tomar el detalle == 100%)

        a = 7 (tamaño maximo que puede tomar el ciclo, [viene de un metodo de el detalle])

        b = 3 (posicion actual)

        c = (b * 100) / a (porcentaje de progreso segun el ciclo)

        - La trazabilidad pasa de manera transparente a ser hecha por detalle de requisicion
        y no por requisicion de acuerdo a ciertas condiciones en el lugar donde se encuentra
        actualmente

"""

from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from .managers import RequisicionManager, ParametrosManager, DetalleRequisicionManager

import re


__all__ = ('Proveedor', 'Requisicion', 'DetalleRequisicion', 'Adjunto', 'Historial', 'Parametros', )


class Proveedor(models.Model):
    """
    Modelo de creación de proveedores en el sistema
    """

    nombre = models.CharField(max_length=255, verbose_name=_('nombre'))
    identificacion = models.BigIntegerField(verbose_name=_('identificación'))
    codigo = models.CharField(max_length=200, verbose_name=_('código'), blank=True)
    correo = models.EmailField(verbose_name=_('email'))
    telefono = models.IntegerField(verbose_name='teléfono', blank=True, null=True)
    celular = models.IntegerField(verbose_name='celular', blank=True, null=True)
    contacto = models.CharField(max_length=255, verbose_name=_('contacto'), blank=True)

    class Meta:
        verbose_name = _('proveedor')
        verbose_name_plural = _('proveedores')

    def __str__(self):
        return 'Proveedor "{0} ({1})"'.format(self.nombre.title(), self.identificacion)


class Requisicion(models.Model):
    """Modelo que guarda las requisiciones que hechas por los empleados."""

    # opciones
    ALTA = 'A'
    MEDIA = 'B'
    BAJA = 'C'

    OPCIONES_PRIORIDAD = (
        (ALTA, 'ALTA'),
        (MEDIA, 'MEDIA'),
        (BAJA, 'BAJA'),
    )

    PENDIENTE = 'PE'
    PROCESO = 'PR'
    TERMINADA = 'TE'
    ANULADA = 'AN'

    OPCIONES_ESTADO = (
        (PENDIENTE, 'PENDIENTE'),
        (PROCESO, 'PROCESO'),
        (TERMINADA, 'TERMINADA'),
        (ANULADA, 'RECHAZADA'),
    )

    EFECTIVO = 'E'
    CREDITO = 'C'

    OPCIONES_FORMA_PAGO = (
        (EFECTIVO, 'EFECTIVO'),
        (CREDITO, 'CRÉDITO'),
    )

    PAGO_PROVEEDOR = 'PP'
    ANTICIPO_PROVEEDOR = 'AP'
    EFECTIVO_PROVEEDOR = 'EP'

    OPCIONES_ESTADO_PAGO = (
        (PAGO_PROVEEDOR, 'PAGO AL PROVEEDOR'),
        (ANTICIPO_PROVEEDOR, 'ANTICIPO AL PROVEEDOR'),
        (EFECTIVO_PROVEEDOR, 'EFECTIVO AL PROVEEDOR'),
    )

    SI = 'SI'
    ESPERA = 'ES'

    OPCIONES_PRESUPUESTO = (
        (SI, 'SI'),
        (ESPERA, 'EN ESPERA'),
    )

    DATA_SET = {
        'digitada': 'Digitada por Empleado y en Jefe de Departamento',
        # 'departamento': 'En Jefe de Departamento',
        'compras': 'En Área de Compras',
        'administrativo': 'En Jefe Administrativo',
        'financiero': 'En Director Financiero',
        'espera_presupuesto': 'A la espera de presupuesto disponible',
        'pago': 'Esperando usuario encargado de pago',
        'presidencia': 'En Presidencia',
        'solicitante': 'Esperando Aprobacion de Solicitante',
        'terminada': 'Requisicion en su etapa finalizada',
        'rechaza_departamento': 'Rechazada por Jefe de Departamento',
        'rechaza_compras': 'Rechazada por Usuario de compras %s',
        'rechaza_administrativo': 'Rechazada por Jefe Administrativo',
        'rechaza_presidencia': 'Rechazada por presidencia'
    }

    # serian los estados de la requisicion que marcan o hacen avance de proceso
    _SUCCESS = [x for x in DATA_SET if not x.startswith('rechaza') and x not in ['digitada', 'espera_presupuesto']]
    # serian los estados de la requisicion que marcan fallas o rechazos
    _FAILED = [x for x in DATA_SET if x.startswith('rechaza')]

    fecha_ingreso = models.DateTimeField(verbose_name=_('fecha de ingreso'), auto_now_add=True)
    empleado = models.ForeignKey('organizacional.Empleado', verbose_name=_('empleado'), on_delete=models.CASCADE)
    observaciones = models.TextField(verbose_name=_('observaciones'))
    asunto = models.CharField(verbose_name=_('asunto'), max_length=255)
    prioridad = models.CharField(max_length=1, verbose_name=_('prioridad'), choices=OPCIONES_PRIORIDAD)
    estado = models.CharField(max_length=2, verbose_name=_('estado'), choices=OPCIONES_ESTADO, default=PENDIENTE)
    fecha_pago = models.DateField(verbose_name=_('fecha de pago'), blank=True, null=True)
    fecha_termina = models.DateField(verbose_name=_('fecha terminada'), blank=True, null=True)
    form_pago = models.CharField(
        max_length=1, verbose_name=_('forma de pago'), blank=True, choices=OPCIONES_FORMA_PAGO
    )
    estado_pago = models.CharField(
        max_length=2, verbose_name=_('estado de pago'), blank=True, choices=OPCIONES_ESTADO_PAGO
    )
    presupuesto_aprobado = models.CharField(
        max_length=2, verbose_name=_('presupuesto aprobado'), blank=True, choices=OPCIONES_PRESUPUESTO
    )

    fecha_solicitud = models.DateField('fecha solicitud recurso', blank=True, null=True)
    fecha_proyeccion = models.DateField('fecha proyección pago', blank=True, null=True)

    objects = RequisicionManager()

    class Meta:
        verbose_name = _('requisición')
        verbose_name_plural = _('requisiciones')

    def __str__(self):
        return "{0}".format(self.id)

    def __len__(self):
        cls = self.__class__
        rastreo = self.get_rastreo()
        # se hace de forma ordenada ascendentemente de acuerdo a el orden de la trazabilidad
        if rastreo == cls.DATA_SET['digitada']:
            return 0
        elif rastreo == cls.DATA_SET['compras']:
            return 1
        elif rastreo == cls.DATA_SET['administrativo']:
            return 2
        elif rastreo == cls.DATA_SET['presidencia']:
            return 3
        elif rastreo == cls.DATA_SET['financiero'] or rastreo == cls.DATA_SET['espera_presupuesto']:
            return 4
        elif rastreo == cls.DATA_SET['pago']:
            return 5
        elif rastreo == cls.DATA_SET['solicitante']:
            return 6
        elif rastreo == cls.DATA_SET['terminada']:
            return 7
        # para los rechazos se trabajará en negativo,
        # ya que si no entraria en los rangos que usan unos templates para cargar los botones
        elif rastreo == cls.DATA_SET['rechaza_departamento']:
            return -1
        elif rastreo == cls.DATA_SET['rechaza_compras']:
            return -2
        elif rastreo == cls.DATA_SET['rechaza_administrativo']:
            return -3
        elif rastreo == cls.DATA_SET['rechaza_presidencia']:
            return -4
        return -5

    def get_position(self):
        cls = self.__class__
        rastreo = self.get_rastreo()
        # se hace de forma ordenada ascendentemente de acuerdo a el orden de la trazabilidad
        if rastreo == cls.DATA_SET['digitada']:
            return 0
        elif rastreo == cls.DATA_SET['compras']:
            return 1
        elif rastreo == cls.DATA_SET['administrativo']:
            return 2
        elif rastreo == cls.DATA_SET['presidencia']:
            return 3
        elif rastreo == cls.DATA_SET['financiero'] or rastreo == cls.DATA_SET['espera_presupuesto']:
            return 4
        elif rastreo == cls.DATA_SET['pago']:
            return 5
        elif rastreo == cls.DATA_SET['solicitante']:
            return 6
        elif rastreo == cls.DATA_SET['terminada']:
            return 7
        # para los rechazos se trabajará en negativo,
        # ya que si no entraria en los rangos que usan unos templates para cargar los botones
        elif rastreo == cls.DATA_SET['rechaza_departamento']:
            return -1
        elif rastreo == cls.DATA_SET['rechaza_compras']:
            return -2
        elif rastreo == cls.DATA_SET['rechaza_administrativo']:
            return -3
        elif rastreo == cls.DATA_SET['rechaza_presidencia']:
            return -4
        return -5

    def crear_historial(self, empleado, estado, observacion=''):
        """
        Método para crear el historial de una requisicion y devuelve el objeto de Historial
        sin guardar
        """
        historia = Historial()
        historia.empleado = empleado
        historia.observacion = observacion
        historia.estado = estado
        historia.requisicion = self
        return historia

    def get_rastreo(self):
        """
        Método de rastreo que determina en que lugar se encuentra actualmente una requisición
        (nombre dado por Google)
        """
        if self.estado == self.__class__.TERMINADA:
            # si está terminada se sale enseguida
            return self.__class__.DATA_SET['terminada']
        if self.historial_set.all():
            # si tiene historial se saca el ultimo
            ultimo = self.historial_set.last()
            # si ya tiene fecha de pago, quiere decir que su proceso está por terminar
            if self.fecha_pago and not self.estado_pago:
                return self.__class__.DATA_SET['pago']
            # siempre y cuando esté aprobada por la ultima persona
            if ultimo.estado == Historial.APROBADA:
                # si la ultima persona en modificar es de compras y ademas es jefe de departamento
                if ultimo.empleado.is_compras and ultimo.empleado.jefe_departamento is True:
                    # si tiene mas de dos historiales ya se encuentra en financiero
                    if self.historial_set.count() >= 3:
                        # si alcanza el tope intercepta presidencia
                        if self.get_total() > Parametros.objects.tope():
                            return self.__class__.DATA_SET['presidencia']
                        return self.__class__.DATA_SET['financiero']
                    # si tiene mas dos historiales está en administrativo
                    if self.historial_set.count() == 2:
                        return self.__class__.DATA_SET['administrativo']
                    # de lo contrario está en compras
                    else:
                        return self.__class__.DATA_SET['compras']
                # si el ultimo fue de pago y tiene fecha de pago y estado de pago
                elif ultimo.empleado.is_usuario_pago and self.fecha_pago and self.estado_pago:
                    return self.__class__.DATA_SET['solicitante']
                # si el ultimo empleado fue el presidente
                elif ultimo.empleado.usuario.has_perm('organizacional.es_presidente'):
                    return self.__class__.DATA_SET['financiero']
                # si el ultimo es jefe financiero
                elif ultimo.empleado.is_jefe_financiero:
                    # si tiene una observacion se pone en espera
                    if ultimo.observacion != '' and self.presupuesto_aprobado == self.__class__.ESPERA:
                        return self.__class__.DATA_SET['espera_presupuesto']
                    # si tiene menos de dos va a compras
                    if self.historial_set.count() < 2:
                        return self.__class__.DATA_SET['compras']
                    # si tiene presupuesto
                    if self.presupuesto_aprobado == self.__class__.SI:
                        # si tiene items con pago en efectivo o cheque(debito)
                        if self.detallerequisicion_set.filter(
                            forma_pago__in=[DetalleRequisicion.EFECTIVO, DetalleRequisicion.DEBITO]
                        ):
                            # se envia a pagos
                            return self.__class__.DATA_SET['pago']
                        # si no se envia a solicitante
                        return self.__class__.DATA_SET['solicitante']
                    # de lo contrario pasa a pago (MOMENTANEAMENTE)
                    return self.__class__.DATA_SET['pago']
                # si el ultimo empleado es jefe administrativo
                # no se tiene en cuenta cuando es == 2 porque solo se da en condicional de arriba
                elif ultimo.empleado.is_jefe_administrativo is True:
                    # si supera el monto establecido pasa a presidencia
                    if self.get_total() > Parametros.objects.tope():
                        return self.__class__.DATA_SET['presidencia']
                    # si tiene mas de dos historiales está en financiero
                    elif self.historial_set.count() > 2:
                        return self.__class__.DATA_SET['financiero']
                    # de lo contrario, está en compras
                    else:
                        return self.__class__.DATA_SET['compras']
                # si es jefe de departamento
                elif ultimo.empleado.jefe_departamento is True:
                    return self.__class__.DATA_SET['compras']
                # si es de compras
                elif ultimo.empleado.is_compras:
                    return self.__class__.DATA_SET['administrativo']
            # si no fue aprobada por la ultima persona
            else:
                # si rechaza la presidencia
                if ultimo.empleado.usuario.has_perm('organizacional:es_presidente'):
                    return self.__class__.DATA_SET['rechaza_presidencia']
                # si rechazo jefe administrativo
                elif ultimo.empleado.is_jefe_administrativo:
                    return self.__class__.DATA_SET['rechaza_administrativo']
                # si rechazo jefe de departamento y es de compras
                elif ultimo.empleado.jefe_departamento is True \
                        and ultimo.empleado.is_compras:
                    return self.__class__.DATA_SET['rechaza_departamento']
                # si rechaza un jefe de departamento
                elif ultimo.empleado.jefe_departamento is True:
                    return self.__class__.DATA_SET['rechaza_departamento']
        # de cualquier otro modo, la requisicion aun no ha sido revisada
        return self.__class__.DATA_SET['digitada']

    @property
    def is_anulada(self):
        """
        Retorna Verdadero si la requisicion fue anulada
        """
        if self.estado == self.__class__.ANULADA or \
           any(self.historial_set.filter(estado=Historial.RECHAZADA)):
            return True
        return False

    def get_total(self):
        """
        Retorna el valor total de la requisicion, con la suma de los totales de todos los detalles
        de la requisicion
        """
        total = 0
        for detalle in self.detallerequisicion_set.all():
            total += detalle.get_valor_total()
        return total

    def get_progreso(self):
        """
        Retorna el progreso general de la requisicion de acuerdo a sus detalles de requisicion
        """
        _progreso = 0
        if self.get_position() >= 0 or \
           self.get_rastreo() in [Requisicion.DATA_SET[x] for x in Requisicion._FAILED]:
            for detalle in self.detallerequisicion_set.all():
                _progreso += detalle.get_progreso()
            return _progreso / self.detallerequisicion_set.count()
        return _progreso

    def get_url_progreso(self):
        """
        Retorna la url de progreso
        """
        base = '%s?check=%d'
        if self.get_rastreo() == Requisicion.DATA_SET['compras']:
            return base % (reverse_lazy('compras:ver_requisiciones_compras'), self.id)
        elif self.get_rastreo() == Requisicion.DATA_SET['administrativo']:
            return base % (reverse_lazy('compras:ver_requisiciones_jefe_administrativo'), self.id)
        elif self.get_rastreo() == Requisicion.DATA_SET['espera_presupuesto']:
            return base % (reverse_lazy('compras:ver_requisiciones_financiero'), self.id)
        return '#'

    def get_url_for_solicitante(self):
        """
        retorna la url del progreso en la vista de el solicitante
        """
        return '%s?check=%d' % (reverse_lazy('compras:ver_requisiciones_empleado'), self.id)


class DetalleRequisicion(models.Model):
    """Modelo que guarda el detalle de una requisición."""

    EFECTIVO = 'E'
    DEBITO = 'D'
    CREDITO = 'C'

    OPCIONES_FORMA_PAGO = (
        (EFECTIVO, 'EFECTIVO'),
        (DEBITO, 'CHEQUE'),
        (CREDITO, 'CRÉDITO'),
    )

    cantidad = models.PositiveIntegerField(verbose_name=_('cantidad'), blank=True, null=True)
    descripcion = models.TextField(verbose_name=_('descripción'))
    referencia = models.CharField(max_length=50, verbose_name=_('referencia'), blank=True)
    marca = models.CharField(max_length=100, verbose_name=_('marca'), blank=True)
    valor_aprobado = models.PositiveIntegerField(verbose_name=_('valor unitario'), blank=True, null=True)
    total_aprobado = models.PositiveIntegerField(verbose_name=_('valor total'), blank=True, null=True)
    forma_pago = models.CharField(_('forma de pago'), choices=OPCIONES_FORMA_PAGO, max_length=1, blank=True)
    requisicion = models.ForeignKey(Requisicion, verbose_name=_('requisición'), on_delete=models.CASCADE)
    cumplida = models.BooleanField(verbose_name=_('cumplida'), default=False)
    proveedor = models.ForeignKey(Proveedor, verbose_name=_('proveedor'), blank=True, null=True, on_delete=models.SET_NULL)

    objects = DetalleRequisicionManager()

    class Meta:
        verbose_name = _('detalle de la requisición')
        verbose_name_plural = _('detalles de la requisición')

    def __str__(self):
        return "Requisicion {0} - {1}".format(self.requisicion, self.id)

    def save(self, *args, **kwargs):
        if not self.cantidad:
            self.cantidad = 1
        if not self.valor_aprobado:
            self.valor_aprobado = 0
        # siempre se guarda el total aprobado (total) de acuerdo al valor unitario y la cantidad
        self.total_aprobado = self.get_valor_total()
        super(DetalleRequisicion, self).save(*args, **kwargs)

    @property
    def is_efectivo(self):
        """
        Retorna verdadero si el tipo de pago de la requisicion es efectivo o cheque
        """
        if self.forma_pago in [self.EFECTIVO, self.DEBITO]:
            return True
        return False

    @property
    def is_credito(self):
        """
        Retorna verdadero si el tipo de pago de la requisicion es crédito
        """
        if not self.is_efectivo:
            return True
        return False

    def get_valor_total(self):
        """
        Retorna el valor total de acuerdo a la cantidad y al valor unitario
        """
        if not self.cantidad:
            self.cantidad = 1
        total = self.cantidad * self.valor_aprobado
        return total

    def get_possible_position(self):
        """
        Retorna la posible cantidad de escalones que tendrá una requisicion
        """
        if self.is_efectivo:
            # si es efectivo y supera la cantidad maxima de dinero
            if self.requisicion.get_total() > Parametros.objects.tope():
                # va a devolver que puede dar todos los pasos posibles
                return len(self.requisicion._SUCCESS)
            # si no, devuelve que no dará el paso a presidencia
            return len(self.requisicion._SUCCESS) - 1
        # si es credito y supera la cantidad maxima de dinero
        if self.requisicion.get_total() > Parametros.objects.tope():
            # dara un paso menos porque no ira a compras
            return len(self.requisicion._SUCCESS) - 1
        # de lo contrario da dos pasos menos porque no irá ni a compras, ni a presidencia
        return len(self.requisicion._SUCCESS) - 2

    def get_actual_position(self):
        """
        Retorna la posicion actual de la requisicion
        """
        # esta funcion NO puede retornar un numero mayor a self.get_possible_position()
        if self.requisicion.DATA_SET['terminada'] != self.requisicion.get_rastreo():
            requisicion_position = self.requisicion.get_position()
            if self.requisicion.is_anulada:
                requisicion_position = abs(self.requisicion.get_position())
            if self.is_efectivo:
                # si es efectivo y va a presidencia
                if self.requisicion.get_total() > Parametros.objects.tope():
                    # cumple todos los pasos asi que puede devolver el paso en que va la requisicion
                    return requisicion_position
                # si no va a presidencia y es mayor que 0
                if requisicion_position > 0:
                    # le resta uno de el paso que no dará
                    return requisicion_position - 1
                # si no, devuelve la posicion en la que está, que es 0 o -1
                return requisicion_position
            # si es credito y va a presidencia
            if self.requisicion.get_total() > Parametros.objects.tope():
                if requisicion_position > 0:
                    # como es credito se le quita un posible paso
                    return requisicion_position - 1
                # si no devuelve la posicion actual que deberia ser 0 o 1
                return requisicion_position
            # si no va a presidencia
            if requisicion_position > 2:  # No se si poner > 2 o >= 2
                # se le deben restar 2 pasos
                return requisicion_position - 2
            # si no devuelve la posicion actual
            return requisicion_position
        # si esta terminada se devuelve la posisicion posible para que no haya errores de calculos
        return self.get_possible_position()

    def get_progreso(self):
        """
        Retorna el valor en porcentaje de progreso de el detalle de la requisicion
        """
        # si no esta cumplida
        if not self.cumplida:
            # si no fue rechazada devuelve el progreso
            if self.requisicion.get_position() >= 0 or \
               self.requisicion.get_rastreo() in [Requisicion.DATA_SET[x] for x in Requisicion._FAILED]:
                _max = self.get_possible_position()
                actual = self.get_actual_position()

                return float((actual * 100) / _max)
            # devuelve 0
            return 0
        # retorna 100%
        return 100


class Adjunto(models.Model):
    """Modelo que guarda los archivos adjuntos que tienen las requisiciones."""

    def ruta_adjuntos(self, filename):
        match = re.compile(r'[a-zA-ZñÑáÁéÉíÍóÓúÚ\s0-9_]')
        data_name = filename.split('.')
        ext = data_name[len(data_name) - 1]
        del data_name[data_name.index(ext)]
        name = ''.join(match.findall(''.join(data_name)))
        filename = name + '.' + ext
        return 'compras/requisicion_{}/{}'.format(self.requisicion.id, filename)

    archivo = models.FileField(verbose_name=_('archivo'), upload_to=ruta_adjuntos)
    requisicion = models.ForeignKey(Requisicion, verbose_name=_('requisición'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('adjunto')
        verbose_name_plural = _('adjuntos')

    def __str__(self):
        return "{0}".format(self.id)

    def get_name(self):
        """
        Retorna el nombre del archivo
        """
        path = self.archivo._get_path().split('/')
        return path[len(path) - 1]


class Historial(models.Model):
    """"Modelo que guarda la historia de cuando y quien modifica una requisicion."""

    # opciones
    APROBADA = 'A'
    RECHAZADA = 'R'
    OPCIONES_ESTADO = (
        (APROBADA, 'Aprobada'),
        (RECHAZADA, 'Rechazada'),
    )

    requisicion = models.ForeignKey(Requisicion, verbose_name=_('requisición'), on_delete=models.CASCADE)
    empleado = models.ForeignKey('organizacional.Empleado', verbose_name=_('empleado'), on_delete=models.CASCADE)
    fecha = models.DateTimeField(verbose_name=_('fecha'), auto_now_add=True)
    observacion = models.TextField(verbose_name=_('observación'), blank=True)
    estado = models.CharField(max_length=1, verbose_name=_('estado'), choices=OPCIONES_ESTADO)

    class Meta:
        verbose_name = _('historial')
        verbose_name_plural = _('historial')

    def __str__(self):
        return "Requisicion {0} - {1}".format(self.requisicion, self.id)


class Parametros(models.Model):
    """
    Modelo para parametrizar ciertos valores de los que dependen los procesos de
    trazabilidad de la aplicacion
    """
    # cuantos dias habiles tiene una requisicion para ser atentida
    dias_habiles = models.PositiveSmallIntegerField(verbose_name=_('dias hábiles'))
    # a partir de que valor, pasa a presidencia
    tope_monto = models.PositiveIntegerField(verbose_name=_('monto tope para presidencia'))

    objects = ParametrosManager()

    class Meta:
        verbose_name = _('parametro')
        verbose_name_plural = _('parametros')

    def __str__(self):
        return '({0})-({1})'.format(self.dias_habiles, self.tope_monto)
