__all__ = ['Action', 'ButtonsGroup']

from enum import auto

from flanautils import FlanaEnum


class Action(FlanaEnum):
    AUTO_WEATHER_CHART = auto()
    MESSAGE_DELETED = auto()


class ButtonsGroup(FlanaEnum):
    CONFIG = auto()
    CONNECT_4 = auto()
    POLL = auto()
    ROLES = auto()
    USERS = auto()
    WEATHER = auto()


class Exchange(FlanaEnum):
    HODLHODL = 'HodlHodl'
    LNP2PBOT = 'lnp2pBot'
    ROBOSATS = 'RoboSats'


class PaymentMethod(FlanaEnum):
    CREDIT_CARD = 'Credit card'
    BIZUM = 'Bizum'
    HALCASH = 'HalCash'
    PAYPAL = 'PayPal'
    REVOLUT = 'Revolut'
    SEPA = 'SEPA'
    SEPA_INSTANT = 'Instant SEPA'
