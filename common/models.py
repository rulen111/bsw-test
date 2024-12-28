import decimal
import enum
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Integer, Numeric, Enum, CheckConstraint
from sqlalchemy.orm import declarative_base, Mapped, mapped_column


class EventState(enum.IntEnum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class PydEvent(BaseModel):
    event_id: int
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None
    state: Optional[EventState] = None


class PydBet(BaseModel):
    bet_id: int
    event_id: int
    amount: decimal.Decimal
    status: EventState = EventState.NEW

    # @field_serializer("amount")
    # def serialize_amount(self, amount: decimal.Decimal, _info):
    #     return str(amount)


Base = declarative_base()


class Bet(Base):
    __tablename__ = "bet"

    bet_id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(Integer())
    amount: Mapped[decimal.Decimal] = mapped_column(Numeric())
    status: Mapped[EventState] = mapped_column(Enum(EventState))

    __table_args__ = (
        CheckConstraint(event_id >= 0, name="check_event_id_non_negative"),
        CheckConstraint(amount > 0, name="check_amount_positive"),
    )
