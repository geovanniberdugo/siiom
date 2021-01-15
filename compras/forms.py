# Django Package
from django.utils.translation import ugettext as _
from django import forms

# Locale Apps
from .models import Requisicion, DetalleRequisicion, Adjunto, Historial, Proveedor


class FormularioSolicitudRequisicion(forms.ModelForm):
    """
    Formulario para la creacion de solicitudes de requisición
    """
    error_css_class = 'has-error'

    class Meta:
        model = Requisicion
        fields = ('observaciones', 'prioridad', 'asunto', 'fecha_solicitud')

    def __init__(self, *args, **kwargs):
        super(FormularioSolicitudRequisicion, self).__init__(*args, **kwargs)
        self.fields['asunto'].widget.attrs.update({'class': 'form-control'})
        self.fields['observaciones'].widget.attrs.update({'class': 'form-control'})
        self.fields['prioridad'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['fecha_solicitud'].widget.attrs.update({'class': 'form-control', 'data-mask': '00/00/00'})


class FormularioDetalleRequisicion(forms.ModelForm):
    """
    Formulario para la creacion de los detalles de la solicitud de requisicion
    """
    error_css_class = 'has-error'

    class Meta:
        model = DetalleRequisicion
        fields = (
            'cantidad', 'descripcion', 'referencia',
            'marca', 'valor_aprobado', 'forma_pago'
        )

    def __init__(self, *args, **kwargs):
        super(FormularioDetalleRequisicion, self).__init__(*args, **kwargs)
        self.fields['cantidad'].widget.attrs.update({'class': 'form-control'})
        self.fields['descripcion'].widget.attrs.update({'class': 'form-control', 'rows': '2'})
        self.fields['referencia'].widget.attrs.update({'class': 'form-control'})
        self.fields['marca'].widget.attrs.update({'class': 'form-control'})
        self.fields['valor_aprobado'].widget.attrs.update({'class': 'form-control'})
        self.fields['forma_pago'].widget.attrs.update({'class': 'form-control'})


class FormularioAdjunto(forms.ModelForm):
    """
    Formulario para la creacion de archivos adjuntos de las requisiciones
    """
    error_css_class = 'has-error'

    class Meta:
        model = Adjunto
        fields = ('archivo', )

    def __init__(self, *args, **kwargs):
        super(FormularioAdjunto, self).__init__(*args, **kwargs)


class FormularioRequisicionesJefe(forms.Form):
    """
    Formulario para las requisiciones que puede aprobar el jefe
    """

    error_css_class = 'has-error'

    id_requisicion = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        super(FormularioRequisicionesJefe, self).__init__(*args, **kwargs)

        self.fields['id_requisicion'].widget = forms.HiddenInput()


class FormularioRequisicionesCompras(forms.Form):
    """
    Formulario para las requisiciones que pueden ver los usuarios de compras
    """

    error_css_class = 'has-error'

    id_requisicion = forms.IntegerField()

    observacion = forms.CharField(widget=forms.Textarea(), required=False)

    def __init__(self, *args, **kwargs):
        super(FormularioRequisicionesCompras, self).__init__(*args, **kwargs)
        self.fields['observacion'].widget.attrs.update({'class': 'form-control'})
        self.fields['id_requisicion'].widget = forms.HiddenInput()

    def clean(self, *args, **kwargs):
        cleaned_data = super(FormularioRequisicionesCompras, self).clean(*args, **kwargs)
        if 'id_requisicion' in cleaned_data and 'observacion' in cleaned_data:
            if 'rechazar' in self.data and cleaned_data['observacion'] == '':
                self.add_error('observacion', _("Este campo debe ser obligatorio"))


class FormularioObservacionHistorial(forms.ModelForm):
    """
    Formulario para la creaciond de observaciones de el historial de una requisicion
    """

    error_css_class = 'has-error'

    class Meta:
        model = Historial
        fields = ('observacion', )

    def __init__(self, *args, **kwargs):
        super(FormularioObservacionHistorial, self).__init__(*args, **kwargs)
        self.fields['observacion'].widget.attrs.update({'class': 'form-control'})


class FormularioFechaPagoRequisicion(forms.ModelForm):
    """
    Formulario que usa el jefe de el departamento financiero para poder dar una fecha
    de pago a una requisicion
    """
    error_css_class = 'has-error'

    observacion = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Requisicion
        fields = ('presupuesto_aprobado', 'fecha_pago', 'fecha_proyeccion')

    def __init__(self, *args, **kwargs):
        super(FormularioFechaPagoRequisicion, self).__init__(*args, **kwargs)
        self.fields['observacion'].widget.attrs.update({'class': 'form-control'})
        self.fields['presupuesto_aprobado'].required = True
        self.fields['presupuesto_aprobado'].widget.attrs.update({'class': 'selectpicker'})
        self.fields['fecha_pago'].label = _('Fecha aprobada de entrega de recurso')
        self.fields['fecha_pago'].required = True
        self.fields['fecha_pago'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_proyeccion'].widget.attrs.update({'class': 'form-control'})

    def clean(self, *args, **kwargs):
        cleaned_data = super(FormularioFechaPagoRequisicion, self).clean(*args, **kwargs)

        if 'presupuesto_aprobado' in cleaned_data:
            if cleaned_data['presupuesto_aprobado'] != Requisicion.SI:
                if 'observacion' in cleaned_data:
                    if cleaned_data['observacion'] is None or cleaned_data['observacion'] == '':
                        self.add_error('observacion', _('Este campo es obligatorio'))
                else:
                    self.add_error('observacion', _('Este campo es obligatorio'))
        return cleaned_data


class FormularioEstadoPago(forms.ModelForm):
    """
    Formulario para dar por terminada una requisicion poniendole un estado de pago
    """
    error_css_class = 'has-error'

    class Meta:
        model = Requisicion
        fields = ('estado_pago', )

    def __init__(self, *args, **kwargs):
        super(FormularioEstadoPago, self).__init__(*args, **kwargs)
        if self.instance:
            if self.instance.fecha_pago is None or self.instance.fecha_pago == '':
                self.fields['estado_pago'].widget.attrs.update(
                    {'class': 'form-control', 'disabled': 'true'}
                )
            else:
                self.fields['estado_pago'].widget.attrs.update({'class': 'selectpicker'})
                self.fields['estado_pago'].required = True


class FormularioEditarValoresDetallesRequisiciones(FormularioDetalleRequisicion):
    """
    Formulario que usan los usuarios de compras y jefe administrativo para poder cada
    valor de el detalle de una requisicion
    """

    class Meta(FormularioDetalleRequisicion.Meta):
        fields = (
            'cantidad', 'descripcion', 'referencia',
            'marca', 'valor_aprobado', 'forma_pago', 'proveedor'
        )

    def __init__(self, *args, **kwargs):
        super(FormularioEditarValoresDetallesRequisiciones, self).__init__(*args, **kwargs)
        self.fields['cantidad'].widget.attrs.update({'readonly': 'readonly'})
        self.fields['descripcion'].widget.attrs.update({'readonly': 'readonly'})
        self.fields['referencia'].widget.attrs.update({'readonly': 'readonly'})
        self.fields['marca'].widget.attrs.update({'readonly': 'readonly'})
        self.fields['proveedor'].widget.attrs.update({'class': 'selectpicker', 'data-live-search': 'true'})


class FormularioEditarValoresJefeAdministrativo(FormularioEditarValoresDetallesRequisiciones):
    """
    Formulario que usa el jefe administrativo, hereda de el de compras, la unica diferencia es que hay
    campos obligatorios
    """

    class Meta(FormularioEditarValoresDetallesRequisiciones.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(FormularioEditarValoresJefeAdministrativo, self).__init__(*args, **kwargs)
        self.fields['forma_pago'].required = True
        self.fields['valor_aprobado'].required = True


class FormularioCumplirDetalleRequisicion(forms.ModelForm):
    """
    Formulario que usa el empleado para poder hacer cumplidas los items de detalles de una
    requisicion hecha por el mismo, e ir aprobando
    """
    class Meta:
        model = DetalleRequisicion
        fields = (
            'cantidad', 'descripcion', 'referencia',
            'marca', 'valor_aprobado', 'forma_pago', 'cumplida'
        )

    def __init__(self, *args, **kwargs):
        super(FormularioCumplirDetalleRequisicion, self).__init__(*args, **kwargs)
        self.fields['cantidad'].widget.attrs.update({'class': 'form-control', 'readonly': 'readonly'})
        self.fields['descripcion'].widget.attrs.update(
            {'class': 'form-control', 'rows': '2', 'readonly': 'readonly'}
        )
        self.fields['referencia'].widget.attrs.update({'class': 'form-control', 'readonly': 'readonly'})
        self.fields['marca'].widget.attrs.update({'class': 'form-control', 'readonly': 'readonly'})
        self.fields['valor_aprobado'].widget.attrs.update({'class': 'form-control', 'readonly': 'readonly'})
        self.fields['forma_pago'].widget.attrs.update({'class': 'form-control', 'disabled': 'true'})
        self.fields['forma_pago'].required = False


class FormularioRangoFechas(forms.Form):
    """
    Formulario Base para el rango de fechas
    """
    error_css_class = 'has-error'

    fecha_inicial = forms.DateField(label=_('Fecha Inicial'))
    fecha_final = forms.DateField(label=_('Fecha Final'))

    def __init__(self, *args, **kwargs):
        super(FormularioRangoFechas, self).__init__(*args, **kwargs)
        self.fields['fecha_inicial'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_final'].widget.attrs.update({'class': 'form-control'})


class FormularioInformeTotalesAreaDerpartamento(FormularioRangoFechas):
    """
    Formulario para el informe de totales por area y departamento
    """

    def __init__(self, *args, **kwargs):
        super(FormularioInformeTotalesAreaDerpartamento, self).__init__(*args, **kwargs)


class FormularioProveedor(forms.ModelForm):
    """
    Formulario para la creacion de proveedores en el sistema
    """
    error_css_class = 'has-error'

    class Meta:
        model = Proveedor
        fields = (
            'nombre', 'identificacion', 'codigo',
            'contacto', 'correo', 'telefono', 'celular'
        )

    def __init__(self, *args, **kwargs):
        super(FormularioProveedor, self).__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({'class': 'form-control'})
        self.fields['identificacion'].widget.attrs.update({'class': 'form-control'})
        self.fields['codigo'].widget.attrs.update({'class': 'form-control'})
        self.fields['contacto'].widget.attrs.update({'class': 'form-control'})
        self.fields['correo'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefono'].widget.attrs.update({'class': 'form-control'})
        self.fields['celular'].widget.attrs.update({'class': 'form-control'})

    def clean(self, *args, **kwargs):
        cleaned_data = super(FormularioProveedor, self).clean(*args, **kwargs)

        if 'telefono' in cleaned_data:
            telefono = cleaned_data['telefono']
        else:
            telefono = None
        if 'celular' in cleaned_data:
            celular = cleaned_data['celular']
        else:
            celular = None

        if not telefono and not celular:
            self.add_error('telefono', _('Este campo debe ser obligatorio'))
            self.add_error('celular', _('Este campo debe ser obligatorio'))

        return cleaned_data
