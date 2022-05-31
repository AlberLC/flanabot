__all__ = ['Punishment']

import datetime
from dataclasses import dataclass
from typing import Callable

from multibot.models import Platform, PunishmentBase, db

from flanabot import constants


@dataclass(eq=False)
class Punishment(PunishmentBase):
    collection = db.punishment

    @classmethod
    async def check_olds(cls, unpunishment_method: Callable, platform: Platform):
        punishment_groups = cls._get_grouped_punishments(platform)

        now = datetime.datetime.now(datetime.timezone.utc)
        for (_, _), sorted_punishments in punishment_groups:
            if not (last_punishment := sorted_punishments[-1]).until or now < last_punishment.until:
                continue

            if last_punishment.until + constants.PUNISHMENTS_RESET <= now:
                for old_punishment in sorted_punishments:
                    old_punishment.delete()

            if last_punishment.is_active:
                await last_punishment.unpunish(unpunishment_method)
                last_punishment.is_active = False
                last_punishment.save()
