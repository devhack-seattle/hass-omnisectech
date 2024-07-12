
import requests
from auth import OmniSecTechAuth

auth=OmniSecTechAuth("rp_markr", "ftk4fna9KMK1rmy_qwv")

a = {"unlock": 3,
     "lock": 2}

def doit(unlock):
    action = a["unlock" if unlock else "lock"]
    data = {
        "DoorElementOperation": {
            "Action": action,
            "Direction": 0,  # not sure what this is
        }
    }

    url = "https://server.omnisectech.com:2580/ISAPI/Bumblebee/ACSPlugin/V0/RemoteControl/DoorElements/8299/Control?MT=PUT"
    r = requests.post(
        url,
        params={"MT": "PUT"},
        json=data,
        # XXX: don't hardcode auth
         # auth=OmniSecTechAuth("rp_markr", "ftk4fna9KMK1rmy_qwv"),
        # auth=requests.auth.HTTPDigestAuth("rp_markr", "ftk4fna9KMK1rmy_qwv"),
        auth=auth,
        verify=False,
    )
    print(r)
    print(r.json())
