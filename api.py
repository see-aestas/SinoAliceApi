from api_base import BaseApi
import json

DEBUG = True


class API(BaseApi):
    def __init__(self):
        BaseApi.__init__(self)


class SigningException(Exception):
    pass
