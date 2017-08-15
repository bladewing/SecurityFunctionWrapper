from enum import Enum

class Type(Enum):
    REGISTER = "/register"
    ATTACK = "/alert"
    KEEPALIVE = "/keep-alive"
    DELETE = "/delete"
