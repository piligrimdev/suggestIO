import os
from dotenv import load_dotenv

import requests
import json
import logging

logger = logging.getLogger(__name__)

class SpotifyAPI:
    def __init__(self, api_key: str):
        self.api_url = 'https://api.spotify.com/v1/'

        self.headers = {
            'Authorization': f'Bearer {api_key}',
            "Accept": "application/json",
            "Content-Type": "application/json"
            # 'Connection': 'keep-alive',
            # 'User-Agent': 'python-requests/2.32.3',
        }

    def _validate_request(request_method):
        def inner1(*args, **kwargs) -> dict | None:
            response = request_method(*args, **kwargs)
            if response.ok:
                logger.debug(f"Request method {request_method} with args({args}) and kwargs({kwargs}) returned code OK")
                return response.json()
            else:
                error_message = response.json()['error']['message']
                logger.debug(f"Request method {request_method} with args({args}) and kwargs({kwargs})"
                             f" returned error: {error_message}")
                raise Exception(error_message)
        return inner1

    @_validate_request
    def user_info(self) -> str:
        return requests.get(f"{self.api_url}me", headers=self.headers)

    @_validate_request
    def audio_features(self, track_id: str) -> requests.Response:
        return requests.get(self.api_url + "audio-features/{0}".format(track_id), headers=self.headers)

    @_validate_request
    def _get_user_saved_tracks(self, next_str: str = None) -> requests.Response:
        payload = {
            "offset": "0",
            "limit": "50"
        }
        if not next_str:
            next_str = self.api_url + "me/tracks"
        return requests.get(next_str, params=payload, headers=self.headers)

    def users_saved_tracks(self):
        track_list = list()
        next_str = None
        while True:
            tracks_json = self._get_user_saved_tracks(next_str)
            for i in tracks_json['items']:
                track_list.append(i['track']["uri"])
            if tracks_json['next'] is not None:
                next_str = tracks_json['next']
            else:
                return track_list

    @_validate_request
    def _get_playlist_tracks(self, playlist_id: int, next_str: str = None) -> requests.Response:
        payload = {
            "fields": "limit,next,items(track(name,uri,artists(uri)))",
            "offset": 0,
            "limit:": 100
        }

        if not next_str:
            next_str = f"{self.api_url}playlists/{playlist_id}/tracks"

        return requests.get(next_str, params=payload, headers=self.headers)

    def playlist_tracks(self, playlist_id: int) -> list[dict]:

        track_list = list()
        next_str = None

        while True:
            playlist_tracks_json = self._get_playlist_tracks(playlist_id, next_str)
            for i in playlist_tracks_json['items']:
                track_list.append({'track': i['track']["uri"], 'artist': i['track']['artists'][0]["uri"]})
            if playlist_tracks_json['next'] is not None:
                next_str = playlist_tracks_json['next']
            else:
                return track_list

    @_validate_request
    def _get_track_recommendation(self, parameters: dict):
        return requests.get(f"{self.api_url}recommendations", params=parameters, headers=self.headers)

    def track_recommendation(self, parameters):
        if "seed_artist" in parameters.keys() or \
                "seed_genres" in parameters.keys() or \
                "seed_tracks" in parameters.keys():
            return self._get_track_recommendation(parameters)
        else:
            raise ValueError("Seed artists, genres, or tracks required")

    @_validate_request
    def _get_related_artists(self, artist_id: int):
        return requests.get(f"{self.api_url}artists/{artist_id}/related-artists", headers=self.headers)

    def related_artists(self, artist_id: int):
        artists_list = []
        rel_artist_json = self._get_related_artists(artist_id)

        for i in rel_artist_json['artists']:
            item = dict()
            item['artist'] = i['id']
            item['genres'] = i['genres']
            artists_list.append(item)

        return artists_list

    @_validate_request
    def _get_artist_genre(self, artist_id: int):
        return requests.get(f"{self.api_url}artists/{artist_id}", headers=self.headers)

    def artist_genre(self, artist_id):
        return self._get_artist_genre(artist_id)

    @_validate_request
    def _get_artist_name(self, artist_id: int):
        return requests.get(f"{self.api_url}artists/{artist_id}", headers=self.headers)

    def artist_name(self, artist_id):
        return self._get_artist_name(artist_id)

    @_validate_request
    def _create_playlist(self, user_id: int, playlist_name: str, public: bool = True, description: str = ""):
        body = {
            "name": playlist_name,
            "public": str(public),
            "description": description
        }

        return requests.post(f"{self.api_url}users/{user_id}/playlists", json=body,
                             headers=self.headers)

    @_validate_request
    def _add_tracks_to_playlis(self, playlist_id: int, tracks_uris: list):
        if len(tracks_uris) > 100:
            raise ValueError("Length of list with tracks per request should be lower or equal to 100")

        return requests.post(f"{self.api_url}playlists/{playlist_id }/tracks",
                             json={"uris": tracks_uris, 'position': '0'}, headers=self.headers)

    def create_playlist(self, user_id: int, playlist_name: str, tracks: list, public: bool =True,
                        description: str =None):

        playlist_id = self._create_playlist(user_id, playlist_name, public, description)['id']

        uris = list()
        for i in tracks:
            if len(uris) != 100:
                uris.append(i)
            else:
                self._add_tracks_to_playlis(playlist_id, uris)
                uris.clear()

        if len(uris) != 0:
            self._add_tracks_to_playlis(playlist_id, uris)

        return playlist_id
