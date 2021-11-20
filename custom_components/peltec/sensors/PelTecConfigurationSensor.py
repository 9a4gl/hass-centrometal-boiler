from typing import List
from .PelTecGenericSensor import PelTecGenericSensor
from homeassistant.components.sensor import SensorEntity


class PelTecConfigurationSensor(PelTecGenericSensor):
    @property
    def native_value(self):
        """Return the value of the sensor."""
        configurations = [
            "1. DHW",
            "2. DHC",
            "3. DHW || DHC",
            "4. BUF",
            "5. DHW || BUF",
            "6. BUF -- IHC",
            "7. DHW || BUF -- IHC",
            "8. BUF -- DHW",
            "9. BUF -- IHC || DHW",
            "10. CRO",
            "11. CRO / BUF",
            "12. DHC || DHW(2)",
            "13. DHC 2X",
            "14. BUF--IHCX2",
            "15. CRO -- DHW",
        ]
        return configurations[int(self.parameter["value"])]

    @staticmethod
    def createEntities(parameters, hass, device) -> List[SensorEntity]:
        entities = []
        entities.append(
            PelTecConfigurationSensor(
                hass,
                device,
                ["", "mdi:state-machine", None, "Configuration"],
                parameters["B_KONF"],
            )
        )
        return entities
