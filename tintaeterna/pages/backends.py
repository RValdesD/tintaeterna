from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailBackend(ModelBackend):
    """Accept a username or email through the existing login field."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None
        identifier = email.strip()
        User = get_user_model()
        if not identifier:
            User().set_password(password)
            return None
        try:
            user = User.objects.get(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            )
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            # Reject ambiguous identities instead of choosing an account.
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
