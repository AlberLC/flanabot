from dataclasses import dataclass

from multibot import User as MultiBotUser, constants as multibot_constants, db

from flanabot.models.punishments import Mute, Punishment


@dataclass(eq=False)
class User(MultiBotUser):
    collection = db.user
    _unique_keys = 'id'

    id: int = None
    name: str = None
    is_admin: bool = None
    original_object: multibot_constants.ORIGINAL_USER = None

    def is_muted_on(self, group_id: int):
        return group_id in self.muted_on

    def is_punished_on(self, group_id: int):
        return group_id in self.punished_on

    @property
    def muted_on(self):
        return {mute.group_id for mute in Mute.find({'user_id': self.id, 'is_active': True})}

    @property
    def punished_on(self):
        return {punishment for punishment in Punishment.find({'user_id': self.id, 'is_active': True})}
