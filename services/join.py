import os
import requests


class Join:
    ICON_SPOTIFY = 'https%3A%2F%2Fwww.iconsdb.com%2Ficons%2Fdownload%2Fwhite%2Fspotify-64.png'

    GROUP_PLAYLIST_UPDATES = 'Spotify - playlist updates'
    GROUP_NEW_RELEASES = 'Spotify - new releases'

    def __init__(self, api_key=None, device_ids=None):
        self.api_key = api_key
        self.device_ids = device_ids

    def notify(self, title, text, group, url, icon_url):
        if self.api_key is not None and self.device_ids is not None:
            requests.get(f'https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?deviceIds={",".join(self.device_ids)}&apikey={self.api_key}' + \
                f'&url={url}&group={group}&title={title}&text={text}&dismissOnTouch=true&icon={icon_url}')
