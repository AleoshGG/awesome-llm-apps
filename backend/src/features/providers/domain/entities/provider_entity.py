from dataclasses import dataclass

@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    address: str
    logo_url: str