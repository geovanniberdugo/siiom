from django.contrib import messages
from django.http import Http404

from waffle import switch_is_active

__author__ = 'German Alzate'


class ViewMessagesMixin(object):
    message_success = 'Se ha agregado un %(model)s nueva.'
    message_error = 'Campos inválidos en el formulario, por favor revise.'

    def form_valid(self, form):
        messages.success(self.request, self.message_success % {'model': str(self.model)})
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, self.message_error)
        return super().form_invalid(form)


class WaffleSwitchMixin(object):
    """
    Checks that as switch is active, or 404. Operates like the FBV decorator waffle_switch
    """
    waffle_switch = None

    def dispatch(self, request, *args, **kwargs):
        if self.waffle_switch.startswith('!'):
            active = not switch_is_active(self.waffle_switch[1:])
        else:
            active = switch_is_active(self.waffle_switch)

        if not active:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
