__all__ = ['Action', 'ButtonsGroup']

from enum import auto

from flanautils import FlanaEnum


class Action(FlanaEnum):
    AUTO_WEATHER_CHART = auto()
    MESSAGE_DELETED = auto()


class ButtonsGroup(FlanaEnum):
    CONFIG = auto()
    POLL = auto()
    ROLES = auto()
    USERS = auto()
    WEATHER = auto()
