from dataclasses import dataclass


@dataclass(frozen=True)
class ClientAudio:
    data: bytes


@dataclass(frozen=True)
class ClientText:
    text: str


@dataclass(frozen=True)
class ClientClose:
    pass


ClientInput = ClientAudio | ClientText | ClientClose
