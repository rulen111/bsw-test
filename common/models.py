import decimal
import enum
from typing import Optional

from pydantic import BaseModel


class EventState(enum.IntEnum):
    NEW = 1
    FINISHED_WIN = 2
    FINISHED_LOSE = 3


class Event(BaseModel):
    event_id: int
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None
    state: Optional[EventState] = None


class Bet(BaseModel):
    bet_id: int
    event_id: int
    amount: decimal.Decimal
    status: EventState = EventState.NEW

    # @field_serializer("amount")
    # def serialize_amount(self, amount: decimal.Decimal, _info):
    #     return str(amount)
