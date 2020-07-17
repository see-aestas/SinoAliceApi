import requests
import json
import msgpack
from Crypto.Util.Padding import pad, unpad
from Crypto.Cipher import AES
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA1, MD5, SHA256
from Crypto.PublicKey import RSA

import hmac
import base64
import time
import random
from urllib.parse import quote_plus
from dataclasses import dataclass

DEBUG = True


def generate_nonce(length=19):
    return int(''.join([str(random.randint(0, 9)) for i in range(length)]))


def generate_device_id():
    return "==" + "".join(
        [random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890") for _ in range(22)])


@dataclass(unsafe_hash=True)
class DeviceInfo:
    appVersion: str = "1.5.0"
    deviceModel: str = "Samsung Galaxy Note10"
    numericCountryCode: int = 840

    carrier: str = "Vodafone"
    country_code: str = "US"
    auth_version: str = "1.4.10"
    store_type: str = "google"
    uaType: str = "android-app"
    currency_code: str = "USD"
    host: str = "bn-payment-us.wrightflyer.net"

    device_header_login_dict = {
        "Authorization": None,
        "X-GREE-GAMELIB": f"authVersion%3D{auth_version}%26storeType%3D{store_type}%26appVersion%3D{appVersion}"
                          f"%26uaType%3D{uaType}%26carrier%3D{carrier}%26compromised%3Dfalse"
                          f"%26countryCode%3D{country_code}%26currencyCode%3D{currency_code}",

        "User-Agent": f"Mozilla/5.0 (Linux; Android 10; {deviceModel} AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36",
        "Content-Type": "application/json; charset=UTF-8",
        "Host": host,
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive"
    }

    device_info_dict = {
        "appVersion": appVersion,
        "urlParam": None,
        "deviceModel": deviceModel,
        "osType": 2,
        "osVersion": "Android OS 10 / API-29",
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
        "uuid": None,
        "xuid": 0,
        "locale": "en_US",
        "numericCountryCode": numericCountryCode
    }


class BaseApi:
    URL = "https://api-sinoalice-us.pokelabo.jp"
    crypto_key = b"***REMOVED***"  # Reverse: Static, Unity part, BasicCrypto.encrypt
    app_secret_payment = "***REMOVED***"  # Reverse: Static, Java Part, .sign.AuthorizedSigner constructor
    app_secret_moderation = "***REMOVED***"
    app_id = "***REMOVED***"  # Reverse: Static, web log

    def __init__(self):
        self.request_session = requests.session()
        self.request_session.verify = False

        self.device_id = generate_device_id()  # Unknown: user generated?, what this is for, but it is okay to generate
        self.uuid_payment = ""  # static, This is in the first response when sending app id
        self.uuid_moderation = ""  # static, This is in the first response when sending app id
        self.x_uid_payment = ""  # static, response to auth/x_uid TODO what is this for
        self.x_uid_moderation = ""  # static, response to auth/x_uid TODO Not used yet + what is this for
        self.private_key_payment = RSA.generate(512)
        self.private_key_moderation = RSA.generate(512)

        self.device_info = DeviceInfo()

        # Use local proxy
        if DEBUG:
            print("Using proxy")
            self.request_session.proxies.update({"http": "http://127.0.0.1:8888", "https": "https://127.0.0.1:8888", })

    def _payment_registration(self):
        base_us_payment_url = "https://bn-payment-us.wrightflyer.net"
        auth_initialize = "/v1.0/auth/initialize"

        device_info_dict = self.device_info.device_info_dict
        device_info_dict["uuid"] = None
        device_info_dict["xuid"] = 0

        login_payload = {
            "device_id": f"{self.device_id}",
            "token": f"{self.private_key_payment.publickey().export_key().decode()}",
            "payload": json.dumps(device_info_dict)
        }


        login_payload_bytes = json.dumps(login_payload)
        authorization = self._build_oauth_header_entry("POST", base_us_payment_url + auth_initialize,
                                                       login_payload_bytes.encode(), self.app_secret_payment, new_account=True)

        header = self.device_info.device_header_login_dict
        header["Authorization"] = authorization
        header["Host"] = base_us_payment_url.rsplit("/", 1)[1]
        self.request_session.headers = header

        response = self.request_session.post(base_us_payment_url + auth_initialize, login_payload_bytes)
        self.uuid_payment = response.json()["uuid"]

        auth_x_uid = "/v1.0/auth/x_uid"
        authorization = self._build_oauth_header_entry("GET", base_us_payment_url + auth_x_uid, b"",self.app_secret_payment,
                                                       rsa_key=self.private_key_payment)

        header["Authorization"] = authorization
        response = self.request_session.get(base_us_payment_url + auth_x_uid)
        self.x_uid_payment = response.json()["x_uid"]

    def _moderation_registration(self):
        base_us_moderation_url = "https://bn-moderation-us.wrightflyer.net"
        auth_initialize = "/v1.0/auth/initialize"

        device_info_dict = self.device_info.device_info_dict
        device_info_dict["uuid"] = self.uuid_payment
        device_info_dict["xuid"] = 0

        login_payload = {
            "device_id": f"{self.device_id}",
            "token": f"{self.private_key_moderation.publickey().export_key().decode()}",
            "payload": json.dumps(device_info_dict)
        }

        login_payload_bytes = json.dumps(login_payload)
        authorization = self._build_oauth_header_entry("POST", base_us_moderation_url + auth_initialize,
                                                       login_payload_bytes.encode(), self.app_secret_moderation, new_account=True)

        self.device_info.device_header_login_dict["X-GREE-GAMELIB"] = "authVersion%3D1.4.10%26appVersion%3D1.5.0%26uaType%3Dandroid-app%26carrier%3DMEDIONmobile%26compromised%3Dfalse%26countryCode%3DUS%26currencyCode%3DUSD"
        header = self.device_info.device_header_login_dict
        header["Authorization"] = authorization
        header["Host"] = base_us_moderation_url.rsplit("/", 1)[1]

        self.request_session.headers = header
        response = self.request_session.post(base_us_moderation_url + auth_initialize, login_payload_bytes)
        self.uuid_moderation = response.json()["uuid"]

    def login(self, new_registration=False):
        if new_registration:
            self._payment_registration()
            self._moderation_registration()



    def _build_oauth_header_entry(self, rest_method: str, full_url: str, body_data: bytes, app_secret, rsa_key=None,
                                  new_account=False):
        timestamp = int(time.time())
        oauth_header = {
            "oauth_body_hash": f"{base64.b64encode(SHA1.new(body_data).digest()).decode()}",
            "oauth_consumer_key": f"{self.app_id}",
            "oauth_nonce": f"{generate_nonce()}",
            "oauth_signature_method": f"{'HMAC-SHA1' if new_account else 'RSA-SHA1'}",
            "oauth_timestamp": f"{timestamp}",
            "oauth_version": "1.0"
        }

        if not new_account:
            to_hash = (app_secret + str(timestamp)).encode()
            param_signature = self._generate_signature(to_hash, SHA1, rsa_key)
            oauth_header["xoauth_as_hash"] = param_signature.strip()
            oauth_header["xoauth_requestor_id"] = self.uuid_payment

        auth_string = ""
        for key, value in sorted(oauth_header.items()):
            if key == "oauth_signature":
                continue
            auth_string += quote_plus(key)
            auth_string += "="
            auth_string += quote_plus(value)
            auth_string += "&"

        string_to_hash = quote_plus(rest_method) + "&" + \
                         quote_plus(full_url) + "&" + \
                         quote_plus(auth_string.rsplit("&", 1)[0])

        if new_account:
            oauth_signature = hmac.new(app_secret.encode(), string_to_hash.encode(), "SHA1").digest()
            oauth_signature = base64.b64encode(oauth_signature)
        else:
            oauth_signature = self._generate_signature(string_to_hash.encode(), SHA1, rsa_key)

        oauth_header["oauth_signature"] = oauth_signature

        oauth_header_entry = "OAuth "
        for key, value in sorted(oauth_header.items()):
            oauth_header_entry += key
            oauth_header_entry += "=\""
            oauth_header_entry += quote_plus(value)
            oauth_header_entry += "\","
        oauth_header_entry = oauth_header_entry[:-1]
        return oauth_header_entry

    def _generate_signature(self, data: bytes, hash_function, key):
        hashed_string = hash_function.new(data)
        signature = pkcs1_15.new(key).sign(hashed_string)
        return base64.b64encode(signature)

    def _decrypt_response(self, response_content: bytes) -> dict:
        iv = response_content[0:16]
        aes = AES.new(self.crypto_key, AES.MODE_CBC, iv)
        pad_text = aes.decrypt(response_content[16:])
        text = unpad(pad_text, 16)
        data_loaded = msgpack.unpackb(text)
        return data_loaded

    def _encrypt_request(self, request_content: bytes):
        request_content = pad(request_content, 16)
        iv = request_content[0:16]  # TODO check if ok
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
        url = BaseApi.URL + resource

        self._prepare_request("GET", resource, {})
        response = self.request_session.get(url, params=params)
        return self._handle_response(response)

    def _post(self, resource, payload: str, remove_header=None):
        url = BaseApi.URL + resource

        self._prepare_request("POST", resource, payload, remove_header=remove_header)

        response = self.request_session.post(url, payload)
        return self._handle_response(response)

    def _put(self):
        pass

    def _delete(self):
        pass


class SigningException(Exception):
    pass
