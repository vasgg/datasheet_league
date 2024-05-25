from enum import StrEnum, auto


class Stage(StrEnum):
    DEV = auto()
    PROD = auto()


class BetStatus(StrEnum):
    INVITED = auto()
    PENDING = auto()
    WIN = auto()
    LOSS = auto()
    CANCELLED = auto()
