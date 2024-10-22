from django.db import models
from django.contrib.auth.models import User
from encrypted_model_fields.fields import EncryptedCharField


class SpotifyAuthData(models.Model):
    # if user is deleted then his tokens should be deleted to
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, unique=True)
    refresh_token = EncryptedCharField(max_length=100)  # refresh token should be stored encrypted
