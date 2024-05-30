from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from enums import BetStatus


class Base(DeclarativeBase):
    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=func.now())


class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    fullname: Mapped[str]
    username: Mapped[str | None] = mapped_column(String(32))
    last_time_checked: Mapped[bool] = mapped_column(default=False, server_default='0')

    def __str__(self):
        return f"User(id={self.id}, fullname={self.fullname}, telegram_id={self.telegram_id})"

    def __repr__(self):
        return self.__str__()


class Event(Base):
    __tablename__ = 'events'

    league: Mapped[str]
    bet_name: Mapped[str]
    worst_odds: Mapped[int]


class Bet(Base):
    __tablename__ = 'bets'

    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'))
    user_telegram_id: Mapped[int] = mapped_column(ForeignKey('users.telegram_id'))
    risk_amount: Mapped[int | None]
    odds: Mapped[int | None]
    result: Mapped[int | None]
    status: Mapped[BetStatus] = mapped_column(default=BetStatus.INVITED, server_default='INVITED')
