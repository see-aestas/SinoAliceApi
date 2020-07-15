import requests
import json
import msgpack
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import hmac
import base64
from Crypto.Hash import SHA1, MD5, SHA256
import time
import random

DEBUG = True
instances = 0


def generate_nonce(length=19):
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


def get_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ")


class API:
    URL = "https://api-sinoalice-us.pokelabo.jp"
    crypto_key = b"***REMOVED***"


    def __init__(self):
        self.request_session = requests.session()
        self.request_session.verify = False
        self.consumer_key = generate_nonce(15) # Like device id

        # Use local proxy
        if DEBUG:
            print("Using proxy")
            self.request_session.proxies.update({"http": "http://127.0.0.1:8888", "https": "https://127.0.0.1:8888", })


    """
    Benutzung von SHA1-RSA-PKCS 
    DefaultSigner wird für den ersten kontakt genommen
    Dann Authoratife für den zweiten (auth/x_uid)
    
    """
    def register_new_account(self):
        oauth_header = self._build_oauth_header()

        pass

    def login(self):
        pass

    def _build_oauth_header(self, body_data:bytes, new_account=False):

        signatur = (httpRequset, secret, treemap)



        ouathHeader = {
            "oauth_body_hash": f"{base64.b64encode(SHA1.new(body_data).digest())}",
            "oauth_consumer_key": f"{self.consumer_key}",
            "oauth_nonce": f"{generate_nonce()}",
            "oauth_signature": "application/json",
            "oauth_signature_method": f"{'HMAC-SHA1' if new_account else 'RSA-SHA1'}",
            "oauth_timestamp": f"{get_timestamp()}",
            "oauth_version": "1.0"
        }
        pass

    def _generate_signatur(self, data: bytes):
        mac = SHA1.new(data).digest()
        return mac

    def _decrypt_response(self, response_content: bytes) -> dict:
        iv = response_content[0:16]
        aes = AES.new(self.crypto_key, AES.MODE_CBC, iv)
        pad_text = aes.decrypt(response_content[16:])
        text = unpad(pad_text, 16)
        data_loaded = msgpack.unpackb(text)
        return data_loaded

    def _encrypt_request(self, request_content: bytes):
        request_content = pad(request_content, 16)
        iv = request_content[0:16] # TODO check if ok
        aes = AES.new(self.crypto_key, AES.MODE_CBC, iv)
        text = aes.encrypt(request_content)
        data_loaded = msgpack.packb(text)
        return iv + data_loaded


    def _prepare_request(self, request_type, resource, data, remove_header=None):
        data = self._encrypt_request(data.encode())
        mac = self._generate_signatur(data)

        exit(1)
        common_headers = {
            "Host": "api-sinoalice-us.pokelabo.jp",
            "User-Agent": "UnityRequest com.nexon.sinoalice 1.0.16 (OnePlus ONEPLUS A6000 Android OS 10 / API-29 (QKQ1.190716.003/2002220019))",
            "X-Unity-Version": "2018.4.19f1",
            "Content-Type": "application/json",
            "Expect": "100-continue",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Cookie": "TODO_Define",
            "X-post-signature": f"{mac}"
        }
        for header in remove_header:
            common_headers.pop(header)

        self.request_session.headers = common_headers

    def _handle_response(self, response):
        decrypted_response = self._decrypt_response(response.content)
        code = response.status_code
        print(decrypted_response)
        return decrypted_response

    def _get(self, resource, params={}):
        url = API.URL + resource

        self._prepare_request("GET", resource, {})
        response = self.request_session.get(url, params=params)
        return self._handle_response(response)

    def _post(self, resource, payload: str, remove_header=None):
        url = API.URL + resource

        self._prepare_request("POST", resource, payload, remove_header=remove_header)

        response = self.request_session.post(url, payload)
        return self._handle_response(response)

    def _put(self):
        pass

    def _delete(self):
        pass

    ########## API ##########
    # a bit sloppy but okay for now

    def POST__api_login(self):
        payload = {
        "payload": {
            "appVersion": "1.0.16",
            "urlParam": None,
            "deviceModel": "OnePlus ONEPLUS A6000",
            "osType": 2,
            "osVersion": "Android OS 10 / API-29 (QKQ1.190716.003/2002220019)",
            "storeType": 2,
            "graphicsDeviceId": 0,
            "graphicsDeviceVendorId": 0,
            "processorCount": 8,
            "processorType": "ARM64 FP ASIMD AES",
            "supportedRenderTargetCount": 8,
            "supports3DTextures": True,
            "supportsAccelerometer": True,
            "supportsComputeShaders": True,
            "supportsGyroscope": True,
            "supportsImageEffects": True,
            "supportsInstancing": True,
            "supportsLocationService": True,
            "supportsRenderTextures": True,
            "supportsRenderToCubemap": True,
            "supportsShadows": True,
            "supportsSparseTextures": True,
            "supportsStencil": 1,
            "supportsVibration": True,
            "uuid": None, # TODO check
            "xuid": 928750150, # TODO check
            "locale": "en_US",
            "numericCountryCode": 826 # TODO check
        },
        "uuid": "***REMOVED***636a36e2c5f747fdb12e059a5f830369", # Todo generate
        "userId": 0,
        "sessionId": "",
        "actionToken": None,
        "ctag": None,
        "actionTime": 132381034208143910
        }

        payload = json.dumps(payload)
        self._post("/api/login", payload, remove_header={'Cookie'})


class SigningException(Exception):
    pass

if __name__ == "__main__":
    a = API()
    a.POST__api_login()