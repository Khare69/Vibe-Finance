import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class AuditLogger:
    """
    Developer telemetry and audit logger.
    Tracks agent latencies, vector search times, document scan metrics,
    and resilience/graceful degradation events.
    """

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.logs: List[Dict[str, Any]] = []

    def log_analysis(
        self,
        ticker: str,
        total_ms: int,
        quant_ms: int,
        rag_ms: int,
        risk_ms: int,
        vector_ms: int,
        documents_scanned: int,
        confidence_score: int,
        degraded_data: bool = False,
        degraded_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        telemetry = {
            "total_execution_ms": total_ms,
            "vector_retrieval_ms": vector_ms,
            "documents_scanned": documents_scanned,
            "confidence_score": confidence_score,
            "degraded_data": degraded_data,
            "degraded_reason": degraded_reason
        }

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticker": ticker,
            "agent_latencies": {
                "quant_ms": quant_ms,
                "rag_ms": rag_ms,
                "risk_ms": risk_ms
            },
            "telemetry": telemetry
        }

        self.logs.append(entry)
        if len(self.logs) > self.max_history:
            self.logs.pop(0)

        return telemetry

    def get_recent_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.logs[-limit:]

audit_logger = AuditLogger()
