__all__ = ['SteamRegion']

from dataclasses import dataclass
from typing import Any

from flanautils import DCMongoBase, FlanaBase


@dataclass
class SteamRegion(DCMongoBase, FlanaBase):
    collection_name = 'steam_region'
    unique_keys = ('code',)

    code: str
    name: str
    flag_url: str
    eur_conversion_rate: float | None = None
    mean_price: float = 0.0

    def __post_init__(self):
        super().__post_init__()
        match self.code:
            case 'eu':
                self.bar_color = '#2b6ced'
                self.bar_line_color = '#0055ff'
            case 'in':
                self.bar_color = '#ffc091'
                self.bar_line_color = '#ff6600'
            case 'ar':
                self.bar_color = '#8adcff'
                self.bar_line_color = '#00b3ff'
            case 'tr':
                self.bar_color = '#ff7878'
                self.bar_line_color = '#ff0000'
            case _:
                self.bar_color = '#68a9f2'
                self.bar_line_color = '#68a9f2'

    def _mongo_repr(self) -> Any:
        return {k: v for k, v in super()._mongo_repr().items() if k in ('code', 'name', 'flag_url')}
