import datetime
import uuid
from uuid import UUID
from typing import Optional, List

from sqlalchemy import create_engine, Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from trading_execution_system.core.config import DATABASE_URL
from trading_execution_system.models.enums import TradeState
from trading_execution_system.models.trade import Trade, TradeDetails, HistoryRecord

Base = declarative_base()


def serialize_data(data):
    if isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    elif isinstance(data, (datetime.date, datetime.datetime)):
        return data.isoformat()
    else:
        return data


class TradeModel(Base):
    """Base Trade model"""

    __tablename__ = "trades"
    id = Column(String, primary_key=True, index=True)
    requester_id = Column(String, nullable=False)
    state = Column(String, nullable=False)
    details = Column(JSON, nullable=False)  # JSON col to store trade details.
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    history = relationship(
        "HistoryModel",
        back_populates="trade",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class HistoryModel(Base):
    __tablename__ = "trade_history"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    trade_id = Column(String, ForeignKey("trades.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    previous_state = Column(String, nullable=False)
    new_state = Column(String, nullable=False)
    details_snapshot = Column(JSON, nullable=False)

    trade = relationship("TradeModel", back_populates="history")


# Create the engine.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
# Create a session factory.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# TODO: CREATE tables using migrations with Alembic
Base.metadata.create_all(bind=engine)


class TradeORMRepository:
    @staticmethod
    def create(trade: Trade) -> Trade:
        with SessionLocal() as db:
            trade_model = TradeModel(
                id=str(trade.id),
                requester_id=trade.requester_id,
                state=trade.state.name,
                details=serialize_data(trade.details.__dict__) if trade.details else {},
            )
            # Add history records.
            for hist in trade.history:
                history_model = HistoryModel(
                    trade_id=str(trade.id),
                    user_id=hist.user_id,
                    action=hist.action,
                    previous_state=hist.previous_state.name,
                    new_state=hist.new_state.name,
                    details_snapshot=serialize_data(hist.details_snapshot),
                    timestamp=hist.timestamp,
                )
                trade_model.history.append(history_model)
            db.add(trade_model)
            db.commit()
            db.refresh(trade_model)
            return trade

    @staticmethod
    def get(trade_id: str) -> Optional[Trade]:
        with SessionLocal() as db:
            # order by updated_at descending to pick the latest record.
            trade_model = (
                db.query(TradeModel)
                .filter(TradeModel.id == trade_id)
                .order_by(TradeModel.updated_at.desc())
                .first()
            )
            if not trade_model:
                return None
            # reconstruct the domain object.
            trade_details = TradeDetails(**trade_model.details)
            trade = Trade(
                id=UUID(trade_model.id),
                requester_id=trade_model.requester_id,
                details=trade_details,
                state=TradeState[trade_model.state],
                history=[],
            )
            for hist in trade_model.history:
                history_record = HistoryRecord(
                    timestamp=hist.timestamp,
                    user_id=hist.user_id,
                    action=hist.action,
                    previous_state=TradeState[hist.previous_state],
                    new_state=TradeState[hist.new_state],
                    details_snapshot=hist.details_snapshot,
                )
                trade.history.append(history_record)
            return trade

    @staticmethod
    def update(trade: Trade) -> None:
        with SessionLocal() as db:
            trade_model = (
                db.query(TradeModel).filter(TradeModel.id == str(trade.id)).first()
            )
            if trade_model:
                trade_model.state = trade.state.name
                trade_model.details = (
                    serialize_data(trade.details.__dict__) if trade.details else {}
                )
                # clear existing history and re-add.
                trade_model.history.clear()
                for hist in trade.history:
                    history_model = HistoryModel(
                        trade_id=str(trade.id),
                        user_id=hist.user_id,
                        action=hist.action,
                        previous_state=hist.previous_state.name,
                        new_state=hist.new_state.name,
                        details_snapshot=serialize_data(hist.details_snapshot),
                        timestamp=hist.timestamp,
                    )
                    trade_model.history.append(history_model)
                db.commit()

    @staticmethod
    def list_all() -> List[Trade]:
        with SessionLocal() as db:
            trades = []
            for trade_model in db.query(TradeModel).all():
                trade_details = TradeDetails(**trade_model.details)
                trade = Trade(
                    id=UUID(trade_model.id),
                    requester_id=trade_model.requester_id,
                    details=trade_details,
                    state=TradeState[trade_model.state],
                    history=[],
                )
                for hist in trade_model.history:
                    history_record = HistoryRecord(
                        timestamp=hist.timestamp,
                        user_id=hist.user_id,
                        action=hist.action,
                        previous_state=TradeState[hist.previous_state],
                        new_state=TradeState[hist.new_state],
                        details_snapshot=hist.details_snapshot,
                    )
                    trade.history.append(history_record)
                trades.append(trade)
            return trades
