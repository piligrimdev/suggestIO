from django.core.management import BaseCommand
from django.contrib.auth.models import User

from suggestio.models import SpotifyAuthData


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.stdout.write("Creating SpotifyAuthData dummy")

        user = User.objects.get(username="pgdev")
        if user:
            spot_token, flag = SpotifyAuthData.objects.get_or_create(user=user,
                                                                     refresh_token="buzz")
            self.stdout.write(f"{spot_token.user.username} {spot_token.refresh_token}")
        else:
            self.stdout.write("No user foudned")
