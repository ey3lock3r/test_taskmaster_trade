from src.models.broker import Broker
from src.models.brokerage_connection import BrokerageConnection
from src.models.user import User
import pytest

def test_create_broker(session):
    broker = Broker(name="TestBroker", base_url="http://test.com", streaming_url="ws://test.com/stream", is_live_mode=False)
    session.add(broker)
    session.commit()
    session.refresh(broker)

    assert broker.id is not None
    assert broker.name == "TestBroker"
    assert broker.base_url == "http://test.com"
    assert broker.streaming_url == "ws://test.com/stream"
    assert broker.is_live_mode is False

def test_broker_name_unique(session):
    broker1 = Broker(name="UniqueBroker", base_url="http://unique.com", streaming_url="ws://unique.com/stream", is_live_mode=False)
    session.add(broker1)
    session.commit()
    session.refresh(broker1)

    with pytest.raises(Exception): # Expecting an integrity error or similar
        broker2 = Broker(name="UniqueBroker", base_url="http://another.com", streaming_url="ws://another.com/stream", is_live_mode=True)
        session.add(broker2)
        session.commit() # This should fail due to unique constraint

def test_broker_brokerage_connection_relationship(session):
    user = User(username="testuser_rel", email="test_rel@example.com", hashed_password="hashedpassword")
    session.add(user)
    session.commit()
    session.refresh(user)

    broker = Broker(name="RelationalBroker", base_url="http://relational.com", streaming_url="ws://relational.com/stream", is_live_mode=True)
    session.add(broker)
    session.commit()
    session.refresh(broker)

    connection = BrokerageConnection(
        user_id=user.id,
        broker_id=broker.id,
        access_token="token123"
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)

    assert connection.broker.id == broker.id
    assert broker.connections[0].id == connection.id