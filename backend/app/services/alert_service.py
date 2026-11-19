"""Alerts-preference service (prototype stub).

The Alert subsystem (creation + dispatch worker) is out of scope for this
prototype. ``set_alert_preference`` records the farmer's opt-in/out intent on
the session trail only; persistence is a documented extension point (add
``farmer.alerts_opted_in`` plus an idempotent ``ALTER TABLE`` when the Alert
subsystem lands).
"""
import logging

logger = logging.getLogger("agriguard.alert_service")


def set_alert_preference(farmer, opted_in: bool) -> None:
    """Stub that logs the farmer's alerts preference intent.

    TODO: persist ``farmer.alerts_opted_in`` once the Farmer model gains that
    column (idempotent migration when the Alert subsystem lands).
    """
    logger.info(
        "Alerts preference recorded (stub): farmer_id=%s opted_in=%s",
        getattr(farmer, "id", None),
        opted_in,
    )
