import asyncio
import websockets
import json
from typing import Dict, List, Optional
from src.config import settings
from src.utils.logger import logger
from src.utils.redis_utils import redis_client

class TradierWebSocketClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.websocket_url = settings.tradier_websocket_url
        self.connection: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.ping_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Establishes a WebSocket connection to Tradier streaming API."""
        try:
            logger.info(f"Connecting to Tradier WebSocket at {self.websocket_url}...")
            self.connection = await websockets.connect(self.websocket_url)
            self.is_connected = True
            logger.info("Tradier WebSocket connected.")
            # Start a background task to send pings
            self.ping_task = asyncio.create_task(self._send_ping())
            await self._authenticate()
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Tradier WebSocket connection closed gracefully.")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Tradier WebSocket connection failed: {e}")
            self.is_connected = False

    async def _authenticate(self):
        """Sends authentication message to the Tradier WebSocket."""
        auth_message = {
            "jsonrpc": "2.0",
            "msg": "auth",
            "data": {
                "access_token": self.access_token
            }
        }
        await self.send_message(auth_message)
        logger.info("Sent authentication message to Tradier WebSocket.")

    async def _send_ping(self):
        """Sends ping messages periodically to keep the connection alive."""
        while self.is_connected:
            try:
                await self.send_message({"jsonrpc": "2.0", "msg": "ping"})
                await asyncio.sleep(30)  # Send ping every 30 seconds
            except websockets.exceptions.ConnectionClosedOK:
                logger.info("Ping task: WebSocket connection closed gracefully.")
                break
            except Exception as e:
                logger.error(f"Ping task: Error sending ping: {e}")
                break

    async def send_message(self, message: Dict):
        """Sends a JSON message over the WebSocket."""
        if self.connection and self.is_connected:
            await self.connection.send(json.dumps(message))
        else:
            logger.warning("WebSocket not connected. Cannot send message.")

    async def subscribe(self, symbols: List[str], channels: List[str]):
        """Subscribes to market data streams."""
        subscribe_message = {
            "jsonrpc": "2.0",
            "msg": "subscribe",
            "data": {
                "symbols": ",".join(symbols),
                "channels": ",".join(channels)
            }
        }
        await self.send_message(subscribe_message)
        logger.info(f"Subscribed to {channels} for symbols: {symbols}")

    async def unsubscribe(self, symbols: List[str], channels: List[str]):
        """Unsubscribes from market data streams."""
        unsubscribe_message = {
            "jsonrpc": "2.0",
            "msg": "unsubscribe",
            "data": {
                "symbols": ",".join(symbols),
                "channels": ",".join(channels)
            }
        }
        await self.send_message(unsubscribe_message)
        logger.info(f"Unsubscribed from {channels} for symbols: {symbols}")

    async def listen_for_messages(self):
        """Listens for incoming messages and processes them."""
        while self.is_connected:
            try:
                message = await self.connection.recv()
                await self._handle_message(json.loads(message))
            except websockets.exceptions.ConnectionClosedOK:
                logger.info("WebSocket connection closed while listening.")
                self.is_connected = False
                break
            except asyncio.CancelledError:
                logger.info("WebSocket listen task cancelled.")
                self.is_connected = False
                break
            except Exception as e:
                logger.error(f"Error receiving or handling WebSocket message: {e}")
                self.is_connected = False
                break

    async def _handle_message(self, message: Dict):
        """Processes incoming WebSocket messages and updates Redis cache."""
        msg_type = message.get("msg")
        data = message.get("data")

        if msg_type == "quote" and data and redis_client:
            symbol = data.get("symbol")
            if symbol:
                # Update individual quote in Redis
                cache_key = f"quotes:{symbol}"
                await redis_client.set(cache_key, json.dumps(data))
                logger.debug(f"Updated quote for {symbol} in Redis.")
        elif msg_type == "option" and data and redis_client:
            symbol = data.get("symbol")
            if symbol:
                # For options, we might need to fetch the full chain or update specific option contracts
                # For simplicity, this example assumes individual option updates.
                # A more robust solution might involve fetching the full chain and updating it.
                cache_key = f"option_chain_contract:{data.get('symbol')}:{data.get('strike')}:{data.get('option_type')}:{data.get('expiration_date')}"
                await redis_client.set(cache_key, json.dumps(data))
                logger.debug(f"Updated option contract for {symbol} in Redis.")
        elif msg_type == "auth" and data:
            if data.get("status") == "ok":
                logger.info("Tradier WebSocket authentication successful.")
            else:
                logger.error(f"Tradier WebSocket authentication failed: {data.get('error')}")
        elif msg_type == "connected":
            logger.info("Tradier WebSocket connection confirmed.")
        elif msg_type == "ping":
            logger.debug("Received ping from Tradier WebSocket.")
        elif msg_type == "unsubscribed":
            logger.info(f"Unsubscribed confirmation: {data}")
        elif msg_type == "error":
            logger.error(f"Tradier WebSocket error: {data.get('error')}")
        else:
            logger.debug(f"Unhandled WebSocket message type: {msg_type} - {message}")

    async def disconnect(self):
        """Closes the WebSocket connection."""
        if self.ping_task:
            self.ping_task.cancel()
            try:
                await self.ping_task
            except asyncio.CancelledError:
                pass
        if self.connection and self.is_connected:
            await self.connection.close()
            self.is_connected = False
            logger.info("Tradier WebSocket disconnected.")