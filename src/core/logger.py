import logging
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict
import sys

SERVICE_NAME = "vinmec-lumina"


class IndustryLogger:
    """
    Structured JSON logger with correlation IDs and PII redaction.
    """
    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        console_handler = logging.StreamHandler(sys.stdout)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, data: Dict[str, Any], correlation_id: str | None = None):
        from src.core.pii_redactor import redact_dict
        safe_data = redact_dict(data)
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": SERVICE_NAME,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "event": event_type,
            "data": safe_data,
        }
        self.logger.info(json.dumps(payload, ensure_ascii=False))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)


# Global logger instance
logger = IndustryLogger()
