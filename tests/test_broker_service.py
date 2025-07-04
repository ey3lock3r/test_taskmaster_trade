from sqlalchemy.orm import Session
from sqlmodel import select # New import
from src.models.broker import Broker
from src.config import BROKER_CONFIGS
from src.services.broker_service import BrokerService
import pytest

# Mock BROKER_CONFIGS for testing purposes
@pytest.fixture
def mock_broker_configs():
    return [
        {"name": "MockBroker1", "base_url": "http://mock1.com", "streaming_url": "ws://mock1.com/stream", "is_live_mode": False},
        {"name": "MockBroker2", "base_url": "http://mock2.com", "streaming_url": "ws://mock2.com/stream", "is_live_mode": True},
    ]

def test_initialize_brokers_adds_new(session, mock_broker_configs):
    # Temporarily override BROKER_CONFIGS for this test
    original_configs = list(BROKER_CONFIGS) # Save original
    BROKER_CONFIGS[:] = mock_broker_configs # Apply mock

    service = BrokerService(session)
    service.initialize_brokers()

    brokers = session.exec(select(Broker)).all()
    assert len(brokers) >= len(mock_broker_configs) # Account for other tests adding brokers
    assert any(b.name == "MockBroker1" for b in brokers)
    assert any(b.name == "MockBroker2" for b in brokers)

    # Restore original configs
    BROKER_CONFIGS[:] = original_configs

def test_initialize_brokers_updates_existing(session):
    # Create an initial broker
    existing_broker = Broker(name="UpdateBroker", base_url="http://old.com", streaming_url="ws://old.com/stream", is_live_mode=False)
    session.add(existing_broker)
    session.commit()
    session.refresh(existing_broker)

    # Temporarily override BROKER_CONFIGS to include an update for this broker
    mock_configs_update = [
        {"name": "UpdateBroker", "base_url": "http://new.com", "streaming_url": "ws://new.com/stream", "is_live_mode": True},
    ]
    original_configs = list(BROKER_CONFIGS)
    BROKER_CONFIGS[:] = mock_configs_update

    service = BrokerService(session)
    service.initialize_brokers()

    updated_broker = session.exec(select(Broker).where(Broker.name == "UpdateBroker")).first()
    assert updated_broker.base_url == "http://new.com"
    assert updated_broker.is_live_mode is True

    # Restore original configs
    BROKER_CONFIGS[:] = original_configs

def test_get_broker_by_name(session):
    broker = Broker(name="FindMeBroker", base_url="http://find.com", streaming_url="ws://find.com/stream", is_live_mode=False)
    session.add(broker)
    session.commit()
    session.refresh(broker)

    service = BrokerService(session)
    found_broker = service.get_broker_by_name("FindMeBroker")
    assert found_broker is not None
    assert found_broker.name == "FindMeBroker"

    not_found_broker = service.get_broker_by_name("NonExistentBroker")
    assert not_found_broker is None

def test_get_all_brokers(session):
    broker1 = Broker(name="AllBroker1", base_url="http://all1.com", streaming_url="ws://all1.com/stream", is_live_mode=False)
    broker2 = Broker(name="AllBroker2", base_url="http://all2.com", streaming_url="ws://all2.com/stream", is_live_mode=True)
    session.add_all([broker1, broker2])
    session.commit()

    service = BrokerService(session)
    all_brokers = service.get_all_brokers()
    
    # Check if the newly added brokers are in the list
    assert any(b.name == "AllBroker1" for b in all_brokers)
    assert any(b.name == "AllBroker2" for b in all_brokers)
    assert len(all_brokers) >= 2 # Ensure at least these two are present