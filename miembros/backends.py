from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmailAuthenticationBackend:
    """
    Backend de autentificación por medio de email.
    """

    def authenticate(self, request, email=None, password=None):
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return None
