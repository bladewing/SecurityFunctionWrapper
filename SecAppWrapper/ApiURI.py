""" Enumeration Class for URIs """
from enum import Enum

class Type(Enum):
    """
    URIs from Documentation of the API to keep it in a central file.
    """
    REGISTER = "/register"
    ATTACK = "/alert"
    KEEPALIVE = "/keep-alive"
    DELETE = "/delete"
