__all__ = ['Punishment']

import datetime
from dataclasses import dataclass
from typing import Any, Callable

from multibot.models import Platform, PunishmentBase, db

from flanabot import constants
from flanabot.models.message import Message


@dataclass(eq=False)
class Punishment(PunishmentBase):
    collection = db.punishment

    level: int = 0

    def _mongo_repr(self) -> Any:
        self_vars = super()._mongo_repr()
        self_vars['level'] = self.level
        return self_vars

    async def apply(self, punishment_method: Callable, unpunishment_method: Callable, message: Message = None):
        self.pull_from_database(overwrite_fields=('level',), exclude_fields=('until',))
        self.level += 1

        await super().apply(punishment_method, unpunishment_method, message)

    @classmethod
    async def check_olds(cls, unpunishment_method: Callable, platform: Platform):
        punishments = cls.find({'platform': platform.value})

        for punishment in punishments:
            now = datetime.datetime.now(datetime.timezone.utc)
            if not punishment.until or now < punishment.until:
                continue

            await punishment.remove(unpunishment_method, delete=False)
            if punishment.is_active:
                punishment.is_active = False
                punishment.last_update = now
                punishment.save()

            if punishment.last_update + constants.PUNISHMENTS_RESET_TIME <= now:
                if punishment.level == 1:
                    punishment.delete()
                else:
                    punishment.level -= 1
                    punishment.last_update = now
                    punishment.save()
