from dataclasses import dataclass


@dataclass
class CreateUploadResponse:
    id: str
    chunk_size: int
