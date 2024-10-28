from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

from suggestio.models import SpotifyAuthData
from suggestio.spotify_api.authentication import SpotifyAuth

from django.core.cache import cache

class CacheAuthorizedUserMixin(UserPassesTestMixin):
    def handle_no_permission(self):
        return redirect('suggestio:spotify-access')

    def cache_token(self, user_a_data):
        u_id = self.request.user.id
        auth_key = cache.get(str(u_id) + '_auth_token')

        if auth_key is None:
            try:
                rToken, auth_key, expires_in = SpotifyAuth().refrsh_auth_token(user_a_data.refresh_token)

                if rToken is not None:
                    user_a_data.refresh_token = rToken
                    user_a_data.save()
            except Exception as e:
                user_a_data.delete()
                return False

            cache.set(str(u_id) + '_auth_token', auth_key, expires_in)
        return True

    def test_func(self):
        user_a_data = SpotifyAuthData.objects.filter(user=self.request.user).first()
        flag = False
        if user_a_data:
            flag = self.cache_token(user_a_data)
        return user_a_data is not None and flag

class DenyAuthorizedUserMixin(UserPassesTestMixin):
    def get_permission_denied_message(self):
        return "You already have spotify permissions."

    def handle_no_permission(self):
        return redirect('suggestio:suggestio-index')

    def test_func(self):
        return not SpotifyAuthData.objects.filter(user=self.request.user).exists()