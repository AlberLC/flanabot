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
        if raw_updated_at := data['updated_at']:
            updated_at = datetime.datetime.fromisoformat(raw_updated_at)
        else:
            updated_at = None

        return cls(offers=data['offers'], updated_at=updated_at)
