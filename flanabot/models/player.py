__all__ = ['Player']

from dataclasses import dataclass

from flanautils import FlanaBase


@dataclass
class Player(FlanaBase):
    id: int
    name: str
    number: int
