__all__ = ['Punishment']

import datetime
from dataclasses import dataclass
from typing import Any

from multibot import Penalty


@dataclass(eq=False)
class Punishment(Penalty):
    collection_name = 'punishment'

    level: int = 0

    def _mongo_repr(self) -> Any:
        self_vars = super()._mongo_repr()
        self_vars['level'] = self.level
        return self_vars

    def delete(self, cascade=False):
        if self.level == 0:
            super().delete(cascade)
        elif self.is_active:
            self.is_active = False
            self.last_update = datetime.datetime.now(datetime.timezone.utc)
            self.save()
