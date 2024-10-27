from django import forms


class CreatePlaylistForm(forms.Form):
    playlist_id = forms.CharField(max_length=40)
