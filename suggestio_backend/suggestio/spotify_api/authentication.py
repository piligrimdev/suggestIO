import os
from dotenv import load_dotenv

import requests
import json

import hashlib
import base64
import string
import random

load_dotenv()

def hash_userid(user_id) -> str:
    dummy_salt = ''.join(random.choices(string.ascii_lowercase +
                             string.punctuation, k=10))
    s_repr = str(user_id) + dummy_salt
    result_hash = hashlib.sha256(s_repr.encode('utf-8')).hexdigest()
    return result_hash

class SpotifyAuth(object):
    def __new__(cls):  # so its singleton
        if not hasattr(cls, 'instance'):
            cls.instance = super(SpotifyAuth, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.redirect = os.getenv('SPOTIFY_REDIRECT_URL', '')
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID', '')
        self._scope = os.getenv('SPOTIFY_SCOPE', '')

        self.headers = {
            'Authorization': 'Bearer {}',
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_auth_link(self, state: str) -> str | None:
        payload = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect,
            'scope': self._scope,
            'state': state
        }

        response =  requests.get("https://accounts.spotify.com/authorize", params=payload)

        if response.ok:
            return response.url
        else:
            raise Exception("Status code of request for auth code is not OK")

    def get_auth_tokens(self, code) -> tuple[str, int]:

        s = "{}:{}".format(self.client_id, os.getenv('SPOTIFY_CLIENT_SECRET', ''))
        utf = s.encode("utf-8")
        byt = base64.b64encode(utf).decode('utf-8')

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect
        }

        headers = self.headers.copy()
        headers['Authorization'] = 'Basic {}'.format(byt)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        data = requests.post('https://accounts.spotify.com/api/token',
                             data=payload, headers=headers)

        if data.ok:
            data_json = data.json()
            refreshToken = data_json['refresh_token']
            authToken = data_json['access_token']
            expires_in = int(data_json['expires_in'])
            return (refreshToken, authToken, expires_in)
        else:
            error = json.loads(data.text)  # should be refactored
            raise Exception(f"Error while retrieving auth tokens:"
                            f" {error['error']}: {error['error_description']}")

    def refrsh_auth_token(self, refresh_token) -> tuple[str, int] | None:
        body = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id
        }

        s = "{}:{}".format(self.client_id, os.getenv('SPOTIFY_CLIENT_SECRET', ''))
        utf = s.encode("utf-8")
        byt = base64.b64encode(utf).decode('utf-8')

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic {}'.format(byt)
        }

        data = requests.post('https://accounts.spotify.com/api/token', headers=headers, params=body)
        js = data.json()
        if data.ok:
            if 'refresh_token' in js.keys():
                new_r_token = js['refresh_token']
            else:
                new_r_token = None
            new_a_token = js['access_token']
            expires_in = int(js['expires_in'])
            return new_r_token, new_a_token, expires_in
        else:
            raise Exception(js['error'])

    def get_user_info(self, token: str) -> str:
        headers = self.headers.copy()
        headers['Authorization'] = f'Bearer {token}'

        data = requests.get('https://api.spotify.com/v1/me', headers=headers)
        js = data.json()
        if data.ok:
            return js['id']
        else:
            return js['error']

