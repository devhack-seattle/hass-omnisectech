""

# jq -r '.ResponseStatus.Data.CryptoResponse | .CryptoKey, .SID'

from typing import Any
import requests
from base64 import b64decode, b64encode
from cryptography.hazmat.primitives.serialization import load_der_public_key
from pydantic import BaseModel, Field, validator
import urllib
import datetime

# This is necessary because hikvision is a fuck
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CryptoResponse(BaseModel):
    SID: str
    CryptoType: int  # Unknown enum presumably
    CryptoMode: int  # Unknown enum presumably
    CryptoKey: str

    def toKey(self):
        decoded = b64decode(self.CryptoKey)
        return load_der_public_key(decoded)

class LoginRequest(BaseModel):
    UserName: str
    Password: str = None
    LoginModel: int = 1 # Unkown enum presumably
    LoginAddress: str = "server.omnisectech.com"

    def fillPass(self, password, key):
        from cryptography.hazmat.primitives.asymmetric import padding

        self.Password = b64encode(
            key.encrypt(
                password.encode(),
                padding=padding.PKCS1v15()
            )
        ).decode()
        return self.Password


class LoginResponse(BaseModel):
    SID: str
    Certificate: str
    UserID: int
    UserType: int
    ClientDomain: str
    MobileGuid: str = Field(alias="MobileGuid ")
    ForwardeDip: str
    VSMSoftWareType: str
    Permission: Any
    HaveInnerSuperPermission: str
    SecurityLibVersion: str
    LocalhostWebClient: int
    ADSLocalhostWebClient: int
    LoginTime: str
    TimeZones: int
    ServiceIP: str
    ServicePort: int
    ServiceWanIP: str
    EncryInfo: Any
    GUID: str
    SlaveSession: Any
    IsUserFirstLogin: int
    WebSessionValidityTime: datetime.timedelta

    @validator('WebSessionValidityTime', pre=True)
    def validitytime_validate(cls, v):
        return datetime.timedelta(minutes=v)



def get_token(username, password):
    r = requests.post("https://server.omnisectech.com:2580/ISAPI/Bumblebee/Platform/V0/Security/Crypto", params={"MT": "GET"}, verify=False)
    if r.json()["ResponseStatus"]["ErrorCode"] != 0:
        raise Exception(r.json())

    crypto = CryptoResponse(**r.json()["ResponseStatus"]["Data"]["CryptoResponse"])



    login_info = LoginRequest(UserName=username)

    login_info.fillPass(password, crypto.toKey())

    r = requests.post(
        "https://server.omnisectech.com:2580/ISAPI/Bumblebee/Platform/V0/Login", 
        params={"SID": crypto.SID, "CT": 0, "MT": "POST"},
        json={"LoginRequest": login_info.dict()},
        verify=False,
    )
    if r.json()["ResponseStatus"]["ErrorCode"] != 0:
        raise Exception(r.json())

    
    return LoginResponse(**r.json()["ResponseStatus"]["Data"]["Login"])
    # return LoginResponse(**r.json()["ResponseStatus"]["Data"]["Login"]).SID


from requests.auth import AuthBase

class OmniSecTechAuth(AuthBase):
    """Attaches OmniSecTech SID to the given Request object."""
    def __init__(self, username, password):
        # setup any auth-related data here
        self._username = username
        self._password = password
        self._expiretime = datetime.datetime.min

    def __call__(self, r):
        self.regen_if_needed()
        r.url += "&" + urllib.parse.urlencode({'SID': self.sid})
        return r

    def regen_if_needed(self):
        if datetime.datetime.now() > self._expiretime:
            response = get_token(self._username, self._password)
            self.sid = response.SID
            self._expiretime = datetime.datetime.now() + response.WebSessionValidityTime

# https://stackoverflow.com/questions/37094419/python-requests-retry-request-after-re-authentication
#   https://docs.aiohttp.org/en/stable/tracing_reference.html#aiohttp.TraceConfig.on_request_end

# {"ResponseStatus":{"ErrorModule":0,"ErrorCode":200}}
# 
# 
# def refresh_token(r, *args, **kwargs):
#     data = r.json()
#     if data["ResponseStatus"]["ErrorCode"] != 0:  # Is there a specific "SID timed out" code?
#         logger.info("Fetching new token as the previous token expired")
#         token = get_token()
#         session.headers.update({"Authorization": f"Bearer {token}"})
#         r.request.headers["Authorization"] = session.headers["Authorization"]
#         return session.send(r.request, verify=False)
# 
# session.hooks['response'].append(refresh_token)
# 
# session = requests.Session()
# session.headers.update({"Authorization": f"Bearer deliberate-wrong-token"})
