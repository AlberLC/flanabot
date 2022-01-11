import datetime
from dataclasses import dataclass

from flanautils import DCMongoBase, FlanaBase
from multibot.models.database import db


@dataclass(eq=False)
class PunishmentBase(DCMongoBase, FlanaBase):
    user_id: int = None
    group_id: int = None
    until: datetime.datetime = None
    is_active: bool = True


@dataclass(eq=False)
class Punishment(PunishmentBase):
    collection = db.punishment


@dataclass(eq=False)
class Mute(PunishmentBase):
    collection = db.mute
