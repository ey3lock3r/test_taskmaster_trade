from sqlmodel import Session, select
from src.models.bot_status import BotStatus
from datetime import datetime, timezone

class BotService:
    def __init__(self, session: Session):
        self.session = session

    def get_bot_status(self) -> BotStatus:
        status = self.session.exec(select(BotStatus)).first()
        if not status:
            status = BotStatus(status="inactive", last_check_in=datetime.now(timezone.utc))
            self.session.add(status)
            self.session.commit()
            self.session.refresh(status)
        return status

    def start_bot(self) -> dict:
        status_record = self.get_bot_status()
        if status_record.status == "active":
            return {"message": "Bot is already running."}
        
        status_record.status = "active"
        status_record.last_check_in = datetime.now(timezone.utc)
        self.session.add(status_record)
        self.session.commit()
        self.session.refresh(status_record)
        return {"message": "Bot started successfully."}

    def stop_bot(self) -> dict:
        status_record = self.get_bot_status()
        if status_record.status == "inactive":
            return {"message": "Bot is already stopped."}
        
        status_record.status = "inactive"
        status_record.last_check_in = datetime.now(timezone.utc)
        self.session.add(status_record)
        self.session.commit()
        self.session.refresh(status_record)
        return {"message": "Bot stopped successfully."}