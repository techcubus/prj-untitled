from ..perception import CONCEPTS


class TasteSensor:
    """
    Gustatory / post-ingestive sense — an interoceptive module, not an exteroceptive sensor.

    Fires on the tick after a consume/drink action and publishes directly to the 'taste'
    bus topic. LimbicSystem subscribes and updates drives accordingly:
      - Good taste → no drive change (hunger already satisfied by behavior engine)
      - Bad taste  → discomfort spike (nausea response)

    The delayed fire mirrors biology: taste and post-ingestive signals arrive
    after the act of eating, allowing memory correction before the next decision.
    """

    def __init__(self, bus):
        self.bus = bus
        self._pending: str | None = None
        bus.subscribe("action", self._on_action)

    def _on_action(self, action) -> None:
        if action.name in ("consume", "drink") and action.target:
            self._pending = action.target

    def tick(self) -> None:
        if self._pending is None:
            return
        target = self._pending
        self._pending = None
        valence = CONCEPTS.get(target, {}).get("valence", 0.5)
        self.bus.publish("taste", {"target": target, "valence": valence})
