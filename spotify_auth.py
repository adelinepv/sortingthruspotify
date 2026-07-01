import os
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth

SCOPE = "user-top-read user-read-recently-played user-library-read"

def get_spotify_client():
    client_id = st.secrets.get("SPOTIFY_CLIENT_ID", os.getenv("SPOTIFY_CLIENT_ID"))
    client_secret = st.secrets.get("SPOTIFY_CLIENT_SECRET", os.getenv("SPOTIFY_CLIENT_SECRET"))
    redirect_uri = st.secrets.get("REDIRECT_URI", os.getenv("REDIRECT_URI"))

    if not client_id or not client_secret or not redirect_uri:
        st.error("Missing Spotify credentials.")
        st.stop()

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        open_browser=False,
        cache_path=".spotify_cache"
    )
    return spotipy.Spotify(auth_manager=auth_manager)