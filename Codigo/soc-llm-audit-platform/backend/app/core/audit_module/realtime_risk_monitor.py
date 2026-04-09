"""
RealtimeRiskMonitor — Daemon Asíncrono de Monitoreo de Riesgos (Sección 12 del Prompt Maestro)

Daemon que ejecuta checks continuos y genera RegulatoryRiskAlerts con
severidad P1-P4, SLA deadlines y acciones automáticas.

Checks:
  - NIS2 SLA breach:     cada 60s  → P1 si breach + auto-notifica CSIRT
  - PII leak detection:  cada 30s  → P1 si PII en respuesta LLM
  - Hallucination rate:  cada 5min → P2 si tasa > 15% en ventana 1h
  - Bias drift:          cada 15min → P3 si desviación > 10%
  - DoW budget:          cada 60s  → P2 si > 80% del presupuesto
"""
import asyncio
import time
import structlog
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from datetime import datetime, UTC

logger = structlog.get_logger()


class AlertSeverity(str, Enum):
    P1_CRITICAL = "P1"
    P2_HIGH = "P2"
    P3_MEDIUM = "P3"
    P4_LOW = "P4"


class RiskCheckType(str, Enum):
    NIS2_SLA_BREACH = "nis2_sla_breach"
    PII_LEAK = "pii_leak_detection"
    HALLUCINATION_RATE = "hallucination_rate"
    BIAS_DRIFT = "bias_drift"
    DOW_BUDGET = "dow_budget"


@dataclass
class RegulatoryRiskAlert:
    check_type: RiskCheckType
    severity: AlertSeverity
    timestamp: float
    message: str
    details: dict = field(default_factory=dict)
    sla_deadline: Optional[str] = None
    auto_action: Optional[str] = None
    resolved: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["check_type"] = self.check_type.value
        d["severity"] = self.severity.value
        return d


class RealtimeRiskMonitor:
    """
    Daemon asíncrono que ejecuta checks regulatorios continuos.
    Diseñado para ejecutarse como tarea de fondo en el lifespan de FastAPI.
    """

    def __init__(self):
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._alerts: list[RegulatoryRiskAlert] = []
        self._subscribers: list = []  # WebSocket broadcast callbacks

        # Estado interno de métricas
        self._metrics = {
            "nis2_incidents": [],         # List of active incidents with timestamps
            "recent_outputs": [],          # Recent LLM outputs for PII scanning
            "hallucination_log": [],       # (timestamp, is_hallucination) tuples
            "bias_baseline": 0.05,         # Baseline disparity
            "bias_current": 0.05,
            "budget_limit_per_hour": 100.0,  # USD
            "budget_current_hour": 0.0,
            "pii_leak_count_today": 0,
        }

    @property
    def active_alerts(self) -> list[dict]:
        return [a.to_dict() for a in self._alerts if not a.resolved]

    @property
    def all_alerts(self) -> list[dict]:
        return [a.to_dict() for a in self._alerts]

    @property
    def metrics_snapshot(self) -> dict:
        now = time.time()
        hour_ago = now - 3600
        hallucinations_1h = [
            h for h in self._metrics["hallucination_log"] if h[0] >= hour_ago
        ]
        total_1h = len(hallucinations_1h)
        hallucination_rate = (
            sum(1 for _, is_h in hallucinations_1h if is_h) / total_1h
            if total_1h > 0
            else 0.0
        )

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "active_alerts_count": len([a for a in self._alerts if not a.resolved]),
            "checks": {
                "nis2_sla": {
                    "active_incidents": len(self._metrics["nis2_incidents"]),
                    "status": "monitoring",
                },
                "pii_leak": {
                    "leaks_today": self._metrics["pii_leak_count_today"],
                    "status": "scanning",
                },
                "hallucination": {
                    "rate_1h": round(hallucination_rate * 100, 2),
                    "threshold": 15.0,
                    "status": "ok" if hallucination_rate < 0.15 else "alert",
                },
                "bias_drift": {
                    "baseline": self._metrics["bias_baseline"],
                    "current": self._metrics["bias_current"],
                    "deviation_pct": round(
                        abs(self._metrics["bias_current"] - self._metrics["bias_baseline"])
                        / max(self._metrics["bias_baseline"], 0.001)
                        * 100,
                        2,
                    ),
                    "threshold_pct": 10.0,
                },
                "dow_budget": {
                    "current_hour_usd": round(self._metrics["budget_current_hour"], 2),
                    "limit_hour_usd": self._metrics["budget_limit_per_hour"],
                    "usage_pct": round(
                        self._metrics["budget_current_hour"]
                        / max(self._metrics["budget_limit_per_hour"], 0.01)
                        * 100,
                        2,
                    ),
                    "threshold_pct": 80.0,
                },
            },
        }

    def register_subscriber(self, callback):
        """Registrar callback para broadcast de alertas vía WebSocket."""
        self._subscribers.append(callback)

    async def _broadcast(self, alert: RegulatoryRiskAlert):
        for callback in self._subscribers:
            try:
                await callback(alert.to_dict())
            except Exception as e:
                logger.warning("Failed to broadcast risk alert", error=str(e))

    # ── External metric update methods ──

    def report_incident(self, incident_id: str, detected_at: float):
        self._metrics["nis2_incidents"].append({
            "id": incident_id,
            "detected_at": detected_at,
            "notified": False,
        })

    def report_llm_output(self, output_text: str, timestamp: Optional[float] = None):
        self._metrics["recent_outputs"].append({
            "text": output_text,
            "timestamp": timestamp or time.time(),
        })
        # Keep last 1000 outputs
        if len(self._metrics["recent_outputs"]) > 1000:
            self._metrics["recent_outputs"] = self._metrics["recent_outputs"][-500:]

    def report_hallucination(self, is_hallucination: bool):
        self._metrics["hallucination_log"].append((time.time(), is_hallucination))
        # Keep last 2h of data
        cutoff = time.time() - 7200
        self._metrics["hallucination_log"] = [
            h for h in self._metrics["hallucination_log"] if h[0] >= cutoff
        ]

    def report_bias_metric(self, disparity: float):
        self._metrics["bias_current"] = disparity

    def report_inference_cost(self, cost_usd: float):
        self._metrics["budget_current_hour"] += cost_usd

    # ── Daemon lifecycle ──

    async def start(self):
        if self._running:
            return
        self._running = True
        logger.info("RealtimeRiskMonitor starting — 5 checks active")
        self._tasks = [
            asyncio.create_task(self._check_loop(self._check_nis2_sla, 60, "NIS2 SLA")),
            asyncio.create_task(self._check_loop(self._check_pii_leak, 30, "PII Leak")),
            asyncio.create_task(self._check_loop(self._check_hallucination, 300, "Hallucination")),
            asyncio.create_task(self._check_loop(self._check_bias_drift, 900, "Bias Drift")),
            asyncio.create_task(self._check_loop(self._check_dow_budget, 60, "DoW Budget")),
            asyncio.create_task(self._budget_reset_loop()),
        ]

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        logger.info("RealtimeRiskMonitor stopped")

    async def _check_loop(self, check_fn, interval_seconds: int, name: str):
        while self._running:
            try:
                await check_fn()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"RiskMonitor check failed: {name}", error=str(e))
            await asyncio.sleep(interval_seconds)

    async def _budget_reset_loop(self):
        """Reset hourly budget counter every 3600s."""
        while self._running:
            await asyncio.sleep(3600)
            self._metrics["budget_current_hour"] = 0.0

    # ── Check implementations ──

    async def _check_nis2_sla(self):
        """Check NIS2 SLA breach — cada 60s. P1 si elapsed > 24h sin notificar CSIRT."""
        now = time.time()
        deadline_24h = 24 * 3600

        for incident in self._metrics["nis2_incidents"]:
            if incident.get("notified"):
                continue
            elapsed = now - incident["detected_at"]
            remaining = deadline_24h - elapsed

            if remaining <= 0:
                alert = RegulatoryRiskAlert(
                    check_type=RiskCheckType.NIS2_SLA_BREACH,
                    severity=AlertSeverity.P1_CRITICAL,
                    timestamp=now,
                    message=f"NIS2 SLA BREACHED: Incident {incident['id']} — 24h exceeded without CSIRT notification",
                    details={
                        "incident_id": incident["id"],
                        "elapsed_hours": round(elapsed / 3600, 2),
                        "deadline_hours": 24,
                    },
                    sla_deadline="24h NIS2 Art.23",
                    auto_action="auto_notify_csirt",
                )
                self._alerts.append(alert)
                incident["notified"] = True
                await self._broadcast(alert)
                logger.critical("NIS2 SLA BREACH", incident_id=incident["id"])
            elif remaining <= 4 * 3600:
                # Pre-alert: 4h before deadline
                alert = RegulatoryRiskAlert(
                    check_type=RiskCheckType.NIS2_SLA_BREACH,
                    severity=AlertSeverity.P2_HIGH,
                    timestamp=now,
                    message=f"NIS2 SLA WARNING: {remaining / 3600:.1f}h remaining for incident {incident['id']}",
                    details={
                        "incident_id": incident["id"],
                        "remaining_hours": round(remaining / 3600, 2),
                    },
                    sla_deadline="24h NIS2 Art.23",
                    auto_action="escalate_soc_lead",
                )
                self._alerts.append(alert)
                await self._broadcast(alert)

    async def _check_pii_leak(self):
        """Check PII leak — cada 30s. P1 si PII detectado en outputs recientes."""
        import re

        pii_patterns = [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",  # Email
            r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",               # IP
            r"\b[0-9]{8}[A-Z]\b",                                      # DNI
            r"\b[XYZ][0-9]{7}[A-Z]\b",                                 # NIE
            r"\b[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{0,4}\b",  # IBAN
        ]

        now = time.time()
        recent = [o for o in self._metrics["recent_outputs"] if now - o["timestamp"] < 60]

        for output in recent:
            for pattern in pii_patterns:
                if re.search(pattern, output["text"]):
                    self._metrics["pii_leak_count_today"] += 1
                    alert = RegulatoryRiskAlert(
                        check_type=RiskCheckType.PII_LEAK,
                        severity=AlertSeverity.P1_CRITICAL,
                        timestamp=now,
                        message="PII LEAK DETECTED in LLM output — GDPR Art.32/33 violation",
                        details={
                            "pattern_matched": pattern,
                            "output_preview": output["text"][:100] + "...",
                            "leaks_today": self._metrics["pii_leak_count_today"],
                        },
                        sla_deadline="72h GDPR Art.33",
                        auto_action="block_output_notify_dpo",
                    )
                    self._alerts.append(alert)
                    await self._broadcast(alert)
                    logger.error("PII leak detected in LLM output")
                    break  # One alert per output

        # Clean old outputs (> 5 min)
        self._metrics["recent_outputs"] = [
            o for o in self._metrics["recent_outputs"] if now - o["timestamp"] < 300
        ]

    async def _check_hallucination(self):
        """Check hallucination rate — cada 5min. P2 si > 15% en ventana 1h."""
        now = time.time()
        hour_ago = now - 3600
        recent = [h for h in self._metrics["hallucination_log"] if h[0] >= hour_ago]

        if len(recent) < 5:  # Need minimum samples
            return

        hallucination_rate = sum(1 for _, is_h in recent if is_h) / len(recent)

        if hallucination_rate > 0.15:
            alert = RegulatoryRiskAlert(
                check_type=RiskCheckType.HALLUCINATION_RATE,
                severity=AlertSeverity.P2_HIGH,
                timestamp=now,
                message=f"HALLUCINATION RATE {hallucination_rate:.1%} exceeds 15% threshold in 1h window",
                details={
                    "rate_1h": round(hallucination_rate * 100, 2),
                    "threshold": 15.0,
                    "samples_1h": len(recent),
                },
                auto_action="pause_model_escalate",
            )
            self._alerts.append(alert)
            await self._broadcast(alert)
            logger.warning("High hallucination rate", rate=hallucination_rate)

    async def _check_bias_drift(self):
        """Check bias drift — cada 15min. P3 si desviación > 10% vs baseline."""
        baseline = self._metrics["bias_baseline"]
        current = self._metrics["bias_current"]

        if baseline <= 0:
            return

        deviation_pct = abs(current - baseline) / baseline * 100

        if deviation_pct > 10.0:
            alert = RegulatoryRiskAlert(
                check_type=RiskCheckType.BIAS_DRIFT,
                severity=AlertSeverity.P3_MEDIUM,
                timestamp=time.time(),
                message=f"BIAS DRIFT detected: {deviation_pct:.1f}% deviation from baseline",
                details={
                    "baseline": baseline,
                    "current": current,
                    "deviation_pct": round(deviation_pct, 2),
                    "threshold_pct": 10.0,
                },
                auto_action="flag_for_review",
            )
            self._alerts.append(alert)
            await self._broadcast(alert)
            logger.warning("Bias drift detected", deviation=deviation_pct)

    async def _check_dow_budget(self):
        """Check Denial-of-Wallet — cada 60s. P2 si gasto > 80% del presupuesto horario."""
        current = self._metrics["budget_current_hour"]
        limit = self._metrics["budget_limit_per_hour"]

        if limit <= 0:
            return

        usage_pct = current / limit * 100

        if usage_pct > 80.0:
            alert = RegulatoryRiskAlert(
                check_type=RiskCheckType.DOW_BUDGET,
                severity=AlertSeverity.P2_HIGH,
                timestamp=time.time(),
                message=f"DoW ALERT: Budget usage at {usage_pct:.1f}% (${current:.2f}/${limit:.2f})",
                details={
                    "current_usd": round(current, 2),
                    "limit_usd": round(limit, 2),
                    "usage_pct": round(usage_pct, 2),
                },
                auto_action="rate_limit_increase",
            )
            self._alerts.append(alert)
            await self._broadcast(alert)
            logger.warning("DoW budget threshold exceeded", usage_pct=usage_pct)


# Singleton instance
risk_monitor = RealtimeRiskMonitor()
