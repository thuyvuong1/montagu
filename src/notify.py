from settings import get_secret
import requests
import json

class Notifier:
    def __init__(self, channel):
        self.enabled = len(channel) > 0
        if self.enabled:
            path = get_secret('slack/deploy-webhook')
            self.url = 'https://hooks.slack.com/services/{}'.format(path)
            self.channel = "#" + channel
            self.username = "montagu-bot"
            self.icon = ":robot_face:"
            self.headers = {'Content-Type': 'application/json'}
    def post(self, message):
        if not self.enabled:
            return
        data = json.dumps({"text": message,
                           "channel": self.channel,
                           "username": self.username,
                           "icon_emoji": self.icon})
        # There are two ways that this can fail: (1) the slack server
        # can respond with an error (e.g., if the incoming webhook is
        # removed or expires, the slack server is down for
        # maintenence but still largely functioning, etc).  In that
        # case we'll get a nice HTTP error code and we can just print
        # that.  (2) the communication with the server fails because
        # the network is down, slack is really down, etc.  In that
        # case requests will Raise and that needs catching.
        #
        # In either case, as soon as one request fails, don't send
        # future notifications as they're highly unlikely to work,
        # and if they're timing out that'll get tedious.
        try:
            r = requests.post(self.url, data=data, headers=self.headers)
            if r.status_code >= 300:
                print("Problem sending message: " + r.reason)
                self.enabled = False
        except Exception as e:
            print("There was a problem sending the slack message:\n{}".format(
                str(e)))
            self.enabled = False
