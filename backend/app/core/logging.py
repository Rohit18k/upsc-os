import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id

        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        if hasattr(record, "audit_action"):
            log_entry["audit"] = {
                "action": record.audit_action,
                "resource": getattr(record, "audit_resource", None),
                "resource_id": getattr(record, "audit_resource_id", None),
                "ip_address": getattr(record, "ip_address", None),
            }

        return json.dumps(log_entry, default=str)


class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

    def log(
        self,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        extra = {
            "audit_action": action,
            "audit_resource": resource,
            "audit_resource_id": resource_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "correlation_id": correlation_id or str(uuid.uuid4()),
        }
        if details:
            extra["audit_details"] = json.dumps(details, default=str)
        self.logger.info(f"Audit: {action} on {resource}", extra=extra)


class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.WARNING)

    def log(
        self,
        event: str,
        severity: str = "warning",
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        extra = {
            "security_event": event,
            "security_severity": severity,
            "ip_address": ip_address,
            "user_id": user_id,
        }
        if details:
            extra["security_details"] = json.dumps(details, default=str)
        self.logger.warning(f"Security: {event}", extra=extra)


audit_logger = AuditLogger()
security_logger = SecurityLogger()


def configure_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.handlers = []
    root_logger.addHandler(handler)

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = []
    uvicorn_logger.addHandler(handler)

    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING)

    return root_logger
