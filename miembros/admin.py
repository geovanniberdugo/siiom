import datetime
from django.contrib import admin
from import_export import resources
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from import_export.admin import ImportExportModelAdmin

from . import models
from .models import Zona, Barrio, TipoMiembro, Miembro, CambioTipo, Escalafon

User = get_user_model()

class DecadeBornListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Login de Usuario'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'llogin'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('hoy', 'Hoy'),
            ('ultima_semana', 'Ultima Semana'),
            ('ultimo_mes', 'Ultimo Mes'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'hoy':
            return queryset.filter(usuario__last_login__icontains=datetime.date.today())
        if self.value() == 'ultima_semana':
            return queryset.filter(
                usuario__last_login__range=(
                    datetime.date.today() - datetime.timedelta(days=7),
                    datetime.date.today() + datetime.timedelta(days=1)
                )
            )
        if self.value() == 'ultimo_mes':
            return queryset.filter(
                usuario__last_login__range=(
                    datetime.date.today() - datetime.timedelta(days=30),
                    datetime.date.today() + datetime.timedelta(days=1)
                )
            )

class FiltroSinEntrar(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Usuarios sin entrar'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'notlogin'

    def lookups(self, request, model_admin):
        return (
            ('none', 'Nunca'),
            ('hoy', 'Hoy'),
            ('ultima_semana', 'Ultima Semana'),
            ('ultimo_mes', 'Ultimo Mes'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'none':
            return queryset.filter(usuario__last_login=None)
        if self.value() == 'hoy':
            return queryset.exclude(usuario__last_login__icontains=datetime.date.today())
        if self.value() == 'ultima_semana':
            return queryset.exclude(
                usuario__last_login__range=(
                    datetime.date.today() - datetime.timedelta(days=7),
                    datetime.date.today() + datetime.timedelta(days=1)
                )
            )
        if self.value() == 'ultimo_mes':
            return queryset.exclude(
                usuario__last_login__range=(
                    datetime.date.today() - datetime.timedelta(days=30),
                    datetime.date.today() + datetime.timedelta(days=1)
                )
            )

class MiembroResource(resources.ModelResource):

    class Meta:
        model = models.Miembro
        import_id_fields = ['cedula']
        fields = ['nombre', 'primer_apellido', 'segundo_apellido', 'genero', 'telefono', 'celular', 'talla', 'fecha_nacimiento', 'cedula', 'direccion', 'barrio', 'email', 'profesion', 'estado_civil', 'conyugue']
        widgets = {
            'conyugue': {'field': 'cedula'}
        }

    def before_save_instance(self, instance, using_transactions, dry_run):
        instance.talla = instance.talla and instance.talla.upper() or ''
        instance.estado = models.Miembro.ACTIVO
        if not dry_run and not instance.usuario_id:
            user = User.objects.create_user(username=instance.cedula, email=instance.email, password=instance.cedula)
            user.groups.add(Group.objects.get(name='Lider'))
            instance.usuario = user

@admin.register(models.Miembro)
class MiembroAdmin(ImportExportModelAdmin):
    resource_class = MiembroResource
    list_select_related = ['usuario']
    list_filter = (DecadeBornListFilter, FiltroSinEntrar)
    list_display = ('id', 'cedula', 'nombre', 'primer_apellido', 'segundo_apellido', 'usuario')
    search_fields = ('cedula', 'nombre', 'primer_apellido', 'segundo_apellido', 'email', 'usuario__username')


class CambioTipoAdmin(admin.ModelAdmin):
    search_fields = ('miembro__nombre', )


admin.site.register(Zona)
admin.site.register(Barrio)
admin.site.register(TipoMiembro)
admin.site.register(CambioTipo, CambioTipoAdmin)
admin.site.register(Escalafon)
