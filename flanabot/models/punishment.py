from dataclasses import dataclass

from multibot.models import Mute, db


@dataclass(eq=False)
class Punishment(Mute):
    collection = db.punishment
