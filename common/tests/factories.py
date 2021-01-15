import factory
from django.contrib.auth import get_user_model, models

def set_admin_permission(obj, created, extracted, **kwargs):
    obj.user_permissions.add(models.Permission.objects.get(codename='es_administrador'))

class UsuarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda o: '%s@siiom.com' % o.username)
    password = factory.PostGenerationMethodCall('set_password', '123456')
    miembro = factory.RelatedFactory('miembros.tests.factories.MiembroFactory', 'usuario')

    class Params:
        admin = factory.Trait(user_permissions=factory.PostGeneration(set_admin_permission))

    @factory.post_generation
    def user_permissions(self, created, extracted, **kwargs):
        if not created:
            return

        if extracted:
            perms = map(lambda o: models.Permission.objects.get(codename=o), extracted)
            self.user_permissions.add(*perms)
