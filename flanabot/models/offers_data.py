import datetime
from dataclasses import dataclass
from typing import Any, Self


@dataclass
class OffersData:
    offers: list[dict[str, Any]]
    updated_at: datetime.datetime | None

    def __bool__(self) -> bool:
        return bool(self.offers)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(offers=data['offers'], updated_at=datetime.datetime.fromisoformat(data['updated_at']))
