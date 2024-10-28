from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

from suggestio.mixins import DenyAuthorizedUserMixin, CacheAuthorizedUserMixin
from suggestio.models import SpotifyAuthData
from suggestio.spotify_api.authentication import hash_userid, SpotifyAuth

from django.core.cache import cache
from django.contrib.auth.models import User

from suggestio.forms import CreatePlaylistForm
from suggestio.spotify_api.spotify_api import SpotifyAPI
from suggestio.spotify_api.suggesion_methods import create_based_playlist

import logging

logger = logging.getLogger(__name__)


class AccessView(LoginRequiredMixin, DenyAuthorizedUserMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:

        u_id = request.user.id

        user_h = hash_userid(u_id)

        cache.set(user_h, u_id, 60*2)
        logger.debug(f'Cached state for user with id={u_id}')

        link = SpotifyAuth().get_auth_link(user_h)

        context = {
            'auth_link': link
        }

        return render(request, 'suggestio/spotify_access.html',
                      context=context)

class CallbackView(LoginRequiredMixin, DenyAuthorizedUserMixin, View):
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
            logger.debug(f"Error occured while retrieving auth link for user with id={request.user.id}:"
                         f" {request.GET.get('error')}")
        else:
            state = request.GET.get('state')  # get state from url
            u_id = cache.get(state) # search for it in cache
            if u_id is None: # if it not founed - either cache expired or state was compromised
                context['error'] = 'Error with state reason.'
                logger.debug(f"State in callback request url does not"
                             f" match cached state for user with id={request.user.id}")
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
                logger.debug(f"Retrieved auth and refresh tokens for user with id={request.user.id}")

        return render(request, 'suggestio/authenticated.html',
                      context=context)

class TestRequestView(LoginRequiredMixin, CacheAuthorizedUserMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        context = dict()
        auth_key = cache.get(str(request.user.id) + '_auth_token')

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

class CreateSuggestionPlaylistView(LoginRequiredMixin, CacheAuthorizedUserMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        auth_key = cache.get(str(request.user.id) + '_auth_token')

        api = SpotifyAPI(auth_key)

        form = CreatePlaylistForm(request.POST)

        context = {'form': form }

        if form.is_valid():
            playlist_id = form.cleaned_data.get('playlist_id')
            try:
                logger.debug(f"Creating suggestions for playlist with id={playlist_id}"
                             f" for user with id={request.user.id}")
                new_playlist_id = create_based_playlist(api, playlist_id, "django playlist",
                                                    True)
                context['link'] = f"https://open.spotify.com/playlist/{new_playlist_id}"
                logger.debug(f"Created playlist for user with id={request.user.id}: {context['link']}")
            except Exception as e:
                context['error'] = e
                logger.debug(f"Error occured on suggestion for user with id={request.user.id}: {e}")

        return render(request, 'suggestio/create_playlist.html', context=context)

    def get(self, request: HttpRequest) -> HttpResponse:
        context = {'form': CreatePlaylistForm()}

        return render(request, 'suggestio/create_playlist.html', context=context)

class IndexView(TemplateView):
    template_name = "suggestio/index.html"
