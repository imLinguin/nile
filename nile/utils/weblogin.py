import logging

webview_available = True

try:
    import webview
except Exception:
    log = logging.getLogger('webview')
    log.debug('Webview unavailable')
    webview_available = False

  
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
