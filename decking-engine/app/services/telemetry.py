"""Multi-threaded background simulation of reefer slot telemetry.

Runs on its own daemon thread, independent of the request/response cycle.
On every tick it generates a temperature/humidity reading for each occupied
Block-R slot; if a reading crosses the safety threshold or simulated power
loss occurs, a high-priority alert is appended to the in-memory alert log
that the dashboard's Alert Ticker polls.
"""

import random
import threading
from datetime import datetime, timezone
from itertools import count

from app.core.config import (
    MAX_ALERTS_RETAINED,
    POWER_LOSS_PROBABILITY,
    REEFER_HUMIDITY_SETPOINT_PCT,
    REEFER_HUMIDITY_TOLERANCE_PCT,
    REEFER_TEMP_CRITICAL_C,
    REEFER_TEMP_SETPOINT_C,
    REEFER_TEMP_TOLERANCE_C,
    TELEMETRY_INTERVAL_SECONDS,
)
from app.models.schemas import Alert, TelemetryReading
from app.services.yard_state import YardState, yard_state


class TelemetrySimulator:
    def __init__(self, yard: YardState) -> None:
        self._yard = yard
        self._lock = threading.RLock()
        self._readings: dict[tuple[str, int, int, int], TelemetryReading] = {}
        self._alerts: list[Alert] = []
        self._alert_id_seq = count(1)
        self._power_state: dict[tuple[str, int, int, int], bool] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="reefer-telemetry")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self._tick()
            self._stop_event.wait(TELEMETRY_INTERVAL_SECONDS)

    def _tick(self) -> None:
        for block, row, bay, tier, occupant in self._yard.occupied_reefer_slots():
            key = (block, row, bay, tier)
            powered = self._power_state.get(key, True)

            if powered and random.random() < POWER_LOSS_PROBABILITY:
                powered = False
            elif not powered and random.random() < 0.3:
                powered = True  # simulated restoration

            self._power_state[key] = powered

            if powered:
                temperature = round(random.gauss(REEFER_TEMP_SETPOINT_C, REEFER_TEMP_TOLERANCE_C / 2), 2)
                humidity = round(random.gauss(REEFER_HUMIDITY_SETPOINT_PCT, REEFER_HUMIDITY_TOLERANCE_PCT / 2), 2)
            else:
                # Power loss: temperature drifts up toward ambient, humidity climbs.
                temperature = round(REEFER_TEMP_CRITICAL_C + random.uniform(2, 8), 2)
                humidity = round(REEFER_HUMIDITY_SETPOINT_PCT + random.uniform(15, 30), 2)

            reading = TelemetryReading(
                block=block,
                row=row,
                bay=bay,
                tier=tier,
                container_id=occupant.container_id,
                temperature_c=temperature,
                humidity_pct=humidity,
                powered=powered,
                timestamp=datetime.now(timezone.utc),
            )

            with self._lock:
                self._readings[key] = reading

            if not powered:
                self._raise_alert(
                    severity="CRITICAL",
                    message=f"Power loss on reefer slot {block}-{row:02d}-{bay:02d} tier {tier} "
                            f"(container {occupant.container_id})",
                    block=block, row=row, bay=bay, tier=tier, container_id=occupant.container_id,
                )
            elif temperature >= REEFER_TEMP_CRITICAL_C:
                self._raise_alert(
                    severity="HIGH",
                    message=f"Temperature threshold breach on {block}-{row:02d}-{bay:02d} tier {tier}: "
                            f"{temperature}C (container {occupant.container_id})",
                    block=block, row=row, bay=bay, tier=tier, container_id=occupant.container_id,
                )

    def _raise_alert(self, severity: str, message: str, block: str, row: int, bay: int, tier: int, container_id: str) -> None:
        alert = Alert(
            id=next(self._alert_id_seq),
            severity=severity,
            message=message,
            block=block,
            row=row,
            bay=bay,
            tier=tier,
            container_id=container_id,
            timestamp=datetime.now(timezone.utc),
        )
        with self._lock:
            self._alerts.append(alert)
            if len(self._alerts) > MAX_ALERTS_RETAINED:
                self._alerts = self._alerts[-MAX_ALERTS_RETAINED:]

    def get_readings(self) -> list[TelemetryReading]:
        with self._lock:
            return list(self._readings.values())

    def get_alerts(self, since_id: int = 0) -> list[Alert]:
        with self._lock:
            return [a for a in self._alerts if a.id > since_id]


telemetry_simulator = TelemetrySimulator(yard_state)
