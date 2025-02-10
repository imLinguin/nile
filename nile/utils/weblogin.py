import datetime
import json
import ssl
from urllib import error, request
from urllib.parse import urlparse, parse_qs

import webview
import os


  
def web_login(url, callback):
    window = webview.create_window('Amazon Login', url)
    def on_loaded():
        url = window.get_current_url()
        print(F"url: {window.get_current_url()}")
        #print(window.)
        print('Page is loaded')
        if url.startswith("https://www.amazon.com/?openid.assoc_handle=amzn_sonic_games_launcher"):
            callback(url)
            window.destroy()  
    window.events.loaded += on_loaded
    webview.start()
