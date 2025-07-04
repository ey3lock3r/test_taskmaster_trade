from sqlmodel import Session, select
from src.models.bot_status import BotStatus
from src.brokerage.interface import BrokerageInterface
from src.brokerage.tradier_adapter import TradierAdapter
from src.models.brokerage_connection import BrokerageConnection
from src.models.broker import Broker # Import Broker model
from src.strategies.pmcc import PMCCStrategy
from src.models.trade_order import TradeOrder # Import TradeOrder model
from src.models.position import Position # Import Position model
from datetime import datetime, timezone
import threading
import time
import asyncio # Import asyncio

class BotService:
    def __init__(self, session: Session, brokerage_adapter: BrokerageInterface = None, strategy: PMCCStrategy = None):
        self.session = session
        # The brokerage_adapter will be initialized in start_bot based on connection_details
        self.brokerage_adapter = brokerage_adapter
        self.strategy = strategy # Strategy will be initialized in start_bot
        self._trading_thread = None
        self._stop_trading_event = threading.Event()

    def get_bot_status(self, bot_instance_id: int) -> BotStatus:
        status = self.session.exec(
            select(BotStatus)
            .where(BotStatus.bot_instance_id == bot_instance_id)
            .order_by(BotStatus.last_check_in.desc()) # Ensure the most recent status is picked
        ).first()
        if not status:
            status = BotStatus(bot_instance_id=bot_instance_id, status="inactive", last_check_in=datetime.now(timezone.utc))
            self.session.add(status)
            self.session.commit()
            self.session.refresh(status)
        return status

    def start_bot(self, bot_instance_id: int, connection_details: BrokerageConnection) -> dict:
        status_record = self.get_bot_status(bot_instance_id)
        if status_record.status == "active":
            return {"message": "Bot is already running."}
        
        # Retrieve the Broker object using the broker_id from connection_details
        broker = self.session.exec(select(Broker).where(Broker.id == connection_details.broker_id)).first()
        if not broker:
            self.handle_bot_error(bot_instance_id, f"Broker with ID {connection_details.broker_id} not found.")
            return {"message": "Failed to start bot: Broker not found.", "status": "error"}

        # Initialize TradierAdapter with both broker and connection
        self.brokerage_adapter = TradierAdapter(broker=broker, connection=connection_details)
        self.strategy = PMCCStrategy(brokerage=self.brokerage_adapter)

        # Connect to brokerage
        if not self.brokerage_adapter.connect(): # connect method no longer needs connection_details
            self.handle_bot_error(bot_instance_id, "Failed to connect to brokerage.")
            return {"message": "Failed to start bot: Could not connect to brokerage.", "status": "error"}

        status_record.status = "active"
        status_record.last_check_in = datetime.now(timezone.utc)
        self.session.add(status_record)
        self.session.commit()
        self.session.refresh(status_record)

        self._stop_trading_event.clear()
        # Run the async trading loop in a new thread
        self._trading_thread = threading.Thread(target=self._run_trading_loop_in_thread, args=(bot_instance_id,))
        self._trading_thread.start()

        return {"message": "Bot started successfully."}

    def stop_bot(self, bot_instance_id: int) -> dict:
        status_record = self.get_bot_status(bot_instance_id)
        if status_record.status == "inactive":
            return {"message": "Bot is already stopped."}
        
        self._stop_trading_event.set()
        if self._trading_thread and self._trading_thread.is_alive():
            self._trading_thread.join(timeout=5) # Wait for the thread to finish

        status_record.status = "inactive"
        status_record.last_check_in = datetime.now(timezone.utc)
        self.session.add(status_record)
        self.session.commit()
        self.session.refresh(status_record)
        return {"message": "Bot stopped successfully."}

    def handle_bot_error(self, bot_instance_id: int, error_message: str) -> dict:
        status_record = self.get_bot_status(bot_instance_id)
        status_record.status = "error"
        status_record.last_check_in = datetime.now(timezone.utc)
        status_record.error_message = error_message # Store the error message
        self.session.add(status_record)
        self.session.commit()
        self.session.refresh(status_record)
        return {"message": f"Bot error handled: {error_message}", "status": "error"}

    def _run_trading_loop_in_thread(self, bot_instance_id: int):
        """Helper to run the async trading loop in a separate thread."""
        asyncio.run(self._run_trading_loop(bot_instance_id))

    async def _run_trading_loop(self, bot_instance_id: int):
        # Placeholder for the main trading loop
        # This loop will continuously run until the stop event is set
        while not self._stop_trading_event.is_set():
            try:
                # Check bot status from DB to ensure it's still active
                status_record = self.get_bot_status(bot_instance_id)
                if status_record.status != "active":
                    self._stop_trading_event.set()
                    break

                # Get market data
                # For PMCC, we need option chain and current price of the underlying
                underlying_symbol = "SPY" # This should eventually come from bot instance parameters
                option_chain = await self.brokerage_adapter.get_option_chain(underlying_symbol)
                current_price_data = await self.brokerage_adapter.get_quotes([underlying_symbol])
                current_price = current_price_data.get(underlying_symbol, {}).get('last') if current_price_data else None

                if not option_chain or not current_price:
                    print(f"Bot {bot_instance_id}: Missing market data for {underlying_symbol}. Skipping analysis.")
                    await asyncio.sleep(5) # Use asyncio.sleep for async functions
                    continue

                market_data = {
                    "option_chain": option_chain,
                    "current_price": current_price,
                    "underlying_symbol": underlying_symbol
                }

                # Analyze market data using the strategy
                if self.strategy.analyze(market_data):
                    print(f"Bot {bot_instance_id}: Trade opportunity identified. Executing strategy...")
                    trade_result = self.strategy.execute() # Assuming execute is synchronous or handles its own async
                    if trade_result.get("status") == "success":
                        print(f"Bot {bot_instance_id}: Trade executed successfully: {trade_result.get('message')}")
                        # Persist trade and position data
                        trade_details = trade_result.get('trade_details')
                        if trade_details:
                            # Save TradeOrder
                            long_order_info = trade_result.get('long_order', {})
                            short_order_info = trade_result.get('short_order', {})

                            trade_order_long = TradeOrder(
                                bot_instance_id=bot_instance_id,
                                symbol=trade_details['underlying_symbol'],
                                order_type="limit", # Assuming limit orders for PMCC
                                quantity=trade_details['num_contracts'],
                                price=trade_details['long_call']['ask'],
                                status=long_order_info.get('status', 'unknown'),
                                executed_at=datetime.now(timezone.utc) if long_order_info.get('status') == 'success' else None
                            )
                            self.session.add(trade_order_long)

                            trade_order_short = TradeOrder(
                                bot_instance_id=bot_instance_id,
                                symbol=trade_details['underlying_symbol'],
                                order_type="limit", # Assuming limit orders for PMCC
                                quantity=trade_details['num_contracts'],
                                price=trade_details['short_call']['bid'],
                                status=short_order_info.get('status', 'unknown'),
                                executed_at=datetime.now(timezone.utc) if short_order_info.get('status') == 'success' else None
                            )
                            self.session.add(trade_order_short)

                            # For simplicity, let's assume a new position is opened or updated.
                            # In a real scenario, you'd check if a position already exists and update it.
                            # For PMCC, it's a spread, so managing individual legs as positions might be complex.
                            # For now, let's just record the underlying position if it's a new one.
                            # This part needs more sophisticated logic for actual position management.
                            # For MVP, we'll just add a placeholder for position update/creation.
                            
                            # Check if a position for the underlying already exists for this bot instance
                            existing_position = self.session.exec(
                                select(Position)
                                .where(Position.bot_instance_id == bot_instance_id)
                                .where(Position.symbol == trade_details['underlying_symbol'])
                            ).first()

                            if existing_position:
                                # Update existing position (simplified: just update current_value)
                                existing_position.current_value = trade_details['net_debit'] # Placeholder
                                existing_position.quantity += trade_details['num_contracts'] # Adjust quantity
                                existing_position.average_cost = (existing_position.average_cost * (existing_position.quantity - trade_details['num_contracts']) + trade_details['net_debit'] * trade_details['num_contracts']) / existing_position.quantity if existing_position.quantity > 0 else 0
                                self.session.add(existing_position)
                                print(f"Bot {bot_instance_id}: Updated existing position for {trade_details['underlying_symbol']}")
                            else:
                                # Create new position
                                new_position = Position(
                                    bot_instance_id=bot_instance_id,
                                    symbol=trade_details['underlying_symbol'],
                                    quantity=trade_details['num_contracts'],
                                    average_cost=trade_details['net_debit'], # Net debit as average cost for the spread
                                    current_value=trade_details['net_debit'] # Initial value
                                )
                                self.session.add(new_position)
                                print(f"Bot {bot_instance_id}: Created new position for {trade_details['underlying_symbol']}")

                            self.session.commit()
                            self.session.refresh(trade_order_long)
                            self.session.refresh(trade_order_short)
                            if existing_position:
                                self.session.refresh(existing_position)
                            else:
                                self.session.refresh(new_position)
                            print(f"Bot {bot_instance_id}: Trade and position data persisted.")
                        else:
                            print(f"Bot {bot_instance_id}: Trade details not available for persistence.")
                    else:
                        print(f"Bot {bot_instance_id}: Trade execution failed: {trade_result.get('message')}")
                else:
                    print(f"Bot {bot_instance_id}: No trade opportunity found.")

                await asyncio.sleep(5) # Poll every 5 seconds
            except Exception as e:
                self.handle_bot_error(bot_instance_id, f"Trading loop error: {str(e)}")
                self._stop_trading_event.set() # Stop the loop on error
                break # Immediately exit the loop on error