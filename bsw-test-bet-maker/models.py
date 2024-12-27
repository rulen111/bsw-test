import decimal

from sqlalchemy import Integer, Numeric, Enum, CheckConstraint
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

from common.models import EventState

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
