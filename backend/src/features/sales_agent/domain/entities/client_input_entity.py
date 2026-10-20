from dataclasses import dataclass


@dataclass(frozen=True)
class ClientAudio:
    data: bytes


@dataclass(frozen=True)
class ClientText:
    text: str


@dataclass(frozen=True)
class ClientImage:
    data: bytes
    mime_type: str


@dataclass(frozen=True)
class ClientClose:
    pass


@dataclass(frozen=True)
class ClientPause:
    pass


@dataclass(frozen=True)
class ClientResume:
    pass


ClientInput = ClientAudio | ClientText | ClientImage | ClientPause | ClientResume | ClientClose
