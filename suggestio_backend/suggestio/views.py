from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect

from suggestio.models import SpotifyAuthData
from suggestio.spotify_api.authentication import hash_userid, SpotifyAuth

from django.core.cache import cache
from django.contrib.auth.models import User

from suggestio.spotify_api.spotify_api import SpotifyAPI


class AccessView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_permission_denied_message(self):
        return "You already have spotify permissions."

    def test_func(self):
        return not SpotifyAuthData.objects.filter(user=self.request.user).exists()


    def get(self, request: HttpRequest) -> HttpResponse:

        u_id = request.user.id

        user_h = hash_userid(u_id)

        cache.set(user_h, u_id, 60*2)

        link = SpotifyAuth().get_auth_link(user_h)

        context = {
            'auth_link': link
        }

        return render(request, 'suggestio/spotify_access.html',
                      context=context)

class CallbackView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get_permission_denied_message(self):
        return self.permission_denied_message

    def test_func(self):
        self.permission_denied_message = "You already have spotify permissions."

        valid_url = False
        if ('code' in self.request.GET.keys() or 'error' in self.request.GET.keys()) \
            and 'state' in self.request.GET.keys():
            valid_url = True
        else:
            self.permission_denied_message = "Invalid callback request."

        return (not SpotifyAuthData.objects.filter(user=self.request.user).exists()) and valid_url

    def get(self, request: HttpRequest) -> HttpResponse:
        context = dict()

        if 'error' in request.GET.keys():
            context['error'] = f"Error occured while retrieving auth link: {request.GET.get('error')}"
        else:
            state = request.GET.get('state')  # get state from url
            u_id = cache.get(state) # search for it in cache
            if u_id is None: # if it not founed - either cache expired or state was compromised
                context['error'] = 'Error with state reason.'
            else:  # if there is one - match it with user and get auth code for it
                cache.delete(state) # delete hash from cache

                # auth user
                rToken, authToken, expires_in = SpotifyAuth().get_auth_tokens(request.GET.get('code'))

                user = User.objects.get(id=u_id)

                user_auth_data, flag = SpotifyAuthData \
                                        .objects \
                                        .get_or_create(user=user)
                user_auth_data.refresh_token = rToken
                user_auth_data.save()

                # save auth_token in cache with expire time
                cache.set(str(u_id) + '_auth_token', authToken, expires_in)
                context['seconds'] = expires_in

        return render(request, 'suggestio/authenticated.html',
                      context=context)

class TestRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    def handle_no_permission(self):
        return redirect('suggestio:spotify-access')

    def test_func(self):
        return SpotifyAuthData.objects.filter(user=self.request.user).exists()

    def get(self, request: HttpRequest) -> HttpResponse:
        context = dict()
        u_id = request.user.id

        auth_key = cache.get(str(u_id) + '_auth_token')

        if auth_key is None:
            # we can be sure that refresh token exists bc we have test_func above
            a_data = SpotifyAuthData.objects.get(user=request.user)

            rToken, auth_key, expires_in = SpotifyAuth().refrsh_auth_token(a_data.refresh_token)

            if rToken is not None:
                a_data.refresh_token = rToken
                a_data.save()

            cache.set(str(u_id) + '_auth_token', auth_key, expires_in)

        content = None
        api = SpotifyAPI(auth_key)

        if request.GET.get('liked_tracks'):
            content = api.users_saved_tracks()
        elif request.GET.get('audio_features'):
            track_id = request.GET.get('audio_features_input')
            if track_id:
                content = api.audio_features(track_id)
        elif request.GET.get('playlist_tracks'):
            playlist_id = request.GET.get('playlist_tracks_input')
            if playlist_id:
                content = api.playlist_tracks(playlist_id)
        elif request.GET.get('track_recommendations'):
            track_id = request.GET.get('track_recommendations_input')
            if track_id:
                content = api.track_recommendation({"seed_tracks": track_id})
        elif request.GET.get('similar_artist'):
            artist_id = request.GET.get('similar_artist_input')
            if artist_id:
                content = api.related_artists(artist_id)

        context['content'] = content

        return render(request, 'suggestio/api_functionality_methods.html', context=context)

