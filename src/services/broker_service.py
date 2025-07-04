from sqlalchemy.orm import Session
from sqlmodel import select # Import select
from src.models.broker import Broker
from src.config import BROKER_CONFIGS # Assuming config will hold initial data

class BrokerService:
    def __init__(self, db: Session):
        self.db = db

    def initialize_brokers(self):
        """
        Loads initial broker configurations into the database.
        Creates new brokers if they don't exist, updates existing ones.
        """
        for config in BROKER_CONFIGS:
            broker = self.db.exec(select(Broker).where(Broker.name == config['name'])).first()
            if not broker:
                broker = Broker(
                    name=config['name'],
                    base_url=config['base_url'],
                    streaming_url=config['streaming_url'], # New field
                    is_live_mode=config['is_live_mode']
                )
                self.db.add(broker)
                print(f"Added new broker: {broker.name}")
            else:
                # Optionally update existing broker details if they change in config
                broker.base_url = config['base_url']
                broker.streaming_url = config['streaming_url'] # Update new field
                broker.is_live_mode = config['is_live_mode']
                print(f"Updated existing broker: {broker.name}")
            self.db.commit()
            self.db.refresh(broker)

    def get_broker_by_name(self, name: str) -> Broker | None:
        return self.db.exec(select(Broker).where(Broker.name == name)).first()

    def get_all_brokers(self) -> list[Broker]:
        return self.db.exec(select(Broker)).all()

    def get_broker_by_id(self, broker_id: int) -> Broker | None:
        return self.db.exec(select(Broker).where(Broker.id == broker_id)).first()