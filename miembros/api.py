from django.contrib.auth.decorators import permission_required
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import JsonResponse

from .forms import DesvincularLiderGrupoForm, ResetearContrasenaAdminForm
from .models import Miembro
from .decorators import user_is_cabeza_red
from common.decorators import login_required_api
from common import constants
from common.api import get_error_forms_to_json


@login_required_api
@user_is_cabeza_red  # No hay soporte con JSON
def desvincular_lider_grupo_api(request, pk):
    """
    Desvincula a un lider de un grupo de amistad
    """

    miembro = get_object_or_404(Miembro.objects.filter(grupo__isnull=False), pk=pk)

    if request.method == 'POST':
        form = DesvincularLiderGrupoForm(data=request.POST)

        if form.is_valid():
            form.desvincular_lider()
            return JsonResponse({'url': reverse('miembros:editar_perfil', args=(miembro.id, ))})
        else:
            errors = get_error_forms_to_json(form)
            return JsonResponse(errors, safe=False)

    return JsonResponse({constants.RESPONSE_CODE: constants.RESPONSE_DENIED})


@login_required_api
@permission_required('miembros.es_administrador', raise_exception=True)
def resetear_contrasena(request):
    """Permite a un administrador resetear la contraseña de un miembro."""

    msg = 'La contraseña se reseteó correctamente y se envió un email al miembro con su nueva contraseña.'
    msg2 = 'La nueva contraseña es la cedula del miembro.'

    if request.method == 'POST':
        form = ResetearContrasenaAdminForm(request.POST)

        if form.is_valid():
            form.resetear()
            return JsonResponse({
                'message': _(msg + msg2),
                constants.RESPONSE_CODE: constants.RESPONSE_SUCCESS
            })

        errors = get_error_forms_to_json(form)
        return JsonResponse(errors, safe=False)

    return JsonResponse({constants.RESPONSE_CODE: constants.RESPONSE_DENIED})
