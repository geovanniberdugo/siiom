from django.db import models
from django.utils import timezone

import datetime


class RequisicionManager(models.Manager):
    """
    Manager para las requisiciones
    """

    def aprobadas_jefe_departamento(self):
        """
        Retorna un QuerySet con las requisiciones aprobadas por jefes
        """
        from .models import Historial
        return (self.filter(
            historial__estado=Historial.APROBADA, historial__empleado__jefe_departamento=True
        ).exclude(estado=self.model.ANULADA) | self.rechazadas_jefe_administrativo()).distinct()

    def rechazadas_jefe_administrativo(self):
        """
        Retorna un Queryset con las requisiciones Rechazadas por el jefe administrativo
        """
        from .models import Historial
        return self.annotate(
            num_historial=models.Count('historial')
        ).filter(
            historial__empleado__areas__departamento__nombre__icontains='administra',
            historial__estado=Historial.RECHAZADA,
            num_historial__gt=2
        )

    def ingresadas_compras(self):
        """
        Retorna un QuerySet con las requisiciones que acaban de entrar a compras
        """
        return self.filter(
            historial__empleado__jefe_departamento=True
        ).exclude(
            estado__in=[self.model.ANULADA, self.model.TERMINADA],
        ).exclude(
            historial__empleado__areas__nombre__icontains='compra'
        ).order_by(
            '-fecha_ingreso', 'prioridad'
        ).distinct()[:5]

    def ingresadas_administrativo(self):
        """
        Retorna un QuerySet con las requisiciones ingresadas en jefe administativo
        """
        return self.annotate(
            num_historial=models.Count('historial')
        ).filter(
            num_historial=2
        ).exclude(
            estado__in=[self.model.ANULADA, self.model.TERMINADA]
        )

    def ingresadas_financiero(self):
        """
        Retorna un Queryset con las requisiciones ingresadas en jefe financiero
        """
        exclude = list(
            self.ingresadas_administrativo().values_list('id', flat=True)
        ) + list(
            self.ingresadas_compras().values_list('id', flat=True)
        )
        query = (self.filter(
            estado=self.model.PROCESO,
        ) | self.filter(
            estado=self.model.PROCESO,
            historial__empleado__usuario__user_permissions__codename='organizacional.es_presidente'
        ) | self.annotate(
            num_historial=models.Count('historial')
        ).filter(
            estado=self.model.PROCESO,
            historial__empleado__usuario__is_superuser=True,
            num_historial=4
        ).exclude(
            id__in=exclude
        )).distinct()
        return [q for q in query if q.get_rastreo() == self.model.DATA_SET['financiero']]

    def ultimo_mes(self, *args, **kwargs):
        """
        Retorna un QuerySet con las requisiciones ingresadas el ultimo mes
        """
        hoy = timezone.now().today()

        return self.filter(
            historial__empleado__jefe_departamento=True,
            fecha_ingreso__range=(
                datetime.date(year=hoy.year, month=hoy.month, day=1),
                hoy + datetime.timedelta(days=1)
            )
        ).filter(*args, **kwargs).distinct()

    def finalizadas_mes(self, *args, **kwargs):
        """
        Retorna un QuerySet con las requisiciones finalizadas en el mes
        """
        hoy = timezone.now()

        return self.filter(
            fecha_termina__range=(
                datetime.date(year=hoy.year, month=hoy.month, day=1),
                hoy + datetime.timedelta(days=1)
            ),
            estado=self.model.TERMINADA
        ).filter(*args, **kwargs)

    def aprobadas_compras(self):
        """
        Retorna un QuerySet con las requisiciones aprobadas por usuario de compras
        """

        return self.annotate(
            num_historial=models.Count('historial')
        ).exclude(num_historial__lt=2, estado=self.model.ANULADA)

    def aprobadas_jefe_administrativo(self):
        """
        Retorna un QuerySet con las requisiciones aprobadas por un jefe administrativo
        """
        # se sacan las requisiciones que tengan mas de 3 historiales y se excluyen las que esten en presidencia
        return self.annotate(
            num_historial=models.Count('historial')
        ).exclude(
            num_historial__lt=3).exclude(
            estado=self.model.ANULADA).exclude(
            id__in=self.en_presidencia().values_list('id', flat=True)  # presidencia es excluido
        )

    def aprobadas_jefe_financiero(self):
        """
        Retorna un Queryset con las requisiciones a las cuales un jefe financiero ha
        puesto una fecha de pago
        """
        # return self.aprobadas_jefe_administrativo().exclude(fecha_pago=None)
        from .models import DetalleRequisicion
        return self.filter(
            presupuesto_aprobado=self.model.SI,
            detallerequisicion__forma_pago__in=[DetalleRequisicion.EFECTIVO, DetalleRequisicion.DEBITO]
        ).exclude(estado=self.model.ANULADA).exclude(fecha_pago=None)

    def en_presidencia(self):
        """
        Retorna un Queryset con las requisiciones que han superado un tope maximo definido
        por los parametros iniciales, siempre y cuando haya sido aprobada por un usuario jefe
        administrativo
        """
        from .models import Parametros

        # se sacan las requisiciones que vallan a presidencia por superar cierto monto
        query_for_total = self.annotate(
            total_valores=models.Sum('detallerequisicion__total_aprobado')
        ).filter(total_valores__gte=Parametros.objects.tope()).values_list('id', flat=True)

        # se sacan las requisiciones que tengan 3 historiales
        query_for_historial = self.annotate(
            num_historial=models.Count('historial')
        ).filter(num_historial=3).values_list('id', flat=True)

        # se hace la intercepcion de los id, es decir las requisiciones que cumplan con las dos condiciones
        query = set(query_for_total) & set(query_for_historial)

        return self.filter(id__in=query)


class ParametrosManager(models.Manager):
    """
    Manager para la clase de parametros
    """

    def dias(self):
        """
        Devuelve el ultimo valor que tenga el campo de dias
        """
        return self.last().dias_habiles

    def tope(self):
        """
        Devuelve el ultimo valor que tenga en el campo de tope de monto
        """
        return self.last().tope_monto


class DetalleRequisicionManager(models.Manager):
    """
    Clase de manager para el modelo de DetalleRequisicion
    """

    def salida_credito_mes(self):
        """
        Retorna la cantidad de dinero que ha salido por items en credito
        """
        hoy = timezone.now().date()

        return self.filter(
            requisicion__historial__fecha__range=(
                datetime.date(year=hoy.year, month=hoy.month, day=1), hoy + datetime.timedelta(days=1)
            ),
            forma_pago=self.model.CREDITO,
            cumplida=True
        ).aggregate(models.Sum('total_aprobado'))

    def salida_efectivo_mes(self):
        """
        Retorna la cantidad de dinero que ha salido por items en efectivo
        """
        hoy = timezone.now().date()

        return self.filter(
            requisicion__historial__fecha__range=(
                datetime.date(year=hoy.year, month=hoy.month, day=1), hoy + datetime.timedelta(days=1)
            ),
            forma_pago__in=[self.model.EFECTIVO, self.model.DEBITO],
            cumplida=True
        ).aggregate(models.Sum('total_aprobado'))
