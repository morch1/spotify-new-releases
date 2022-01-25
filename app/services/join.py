import os
import requests


class Join:
    def __init__(self, api_key=None, device_ids=None):
        self.api_key = api_key
        self.device_ids = device_ids

    def notify(self, title: str, text: str, group: str, url: str, icon_url: str):
        if self.api_key is not None and self.device_ids is not None:
            requests.get(f'https://joinjoaomgcd.appspot.com/_ah/api/messaging/v1/sendPush?deviceIds={",".join(self.device_ids)}&apikey={self.api_key}' + \
                f'&url={url}&group={group}&title={title}&text={text}&dismissOnTouch=true&icon={icon_url}')
