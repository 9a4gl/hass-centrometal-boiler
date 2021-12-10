from typing import List
from homeassistant.components.sensor import SensorEntity

from .PelTecGenericSensor import PelTecGenericSensor


class PelTecWorkingTableSensor(PelTecGenericSensor):
    def __init__(self, hass, device, sensor_data, param):
        super().__init__(hass, device, sensor_data, param)
        for tableIndex in range(1, 4):
            for i in range(0, 42):
                name = "PVAL_" + str(222 + tableIndex) + "_" + str(i)
                parameter = self.device.getOrCreatePelTecParameter(name)
                parameter["used"] = True

    def __del__(self):
        for tableIndex in range(1, 4):
            for i in range(0, 42):
                name = "PVAL_" + str(222 + tableIndex) + "_" + str(i)
                parameter = self.device.getOrCreatePelTecParameter(name)
                parameter.set_update_callback(None, "table")

    async def async_added_to_hass(self):
        """Subscribe to sensor events."""
        await super().async_added_to_hass()
        for tableIndex in range(1, 4):
            for i in range(0, 42):
                name = "PVAL_" + str(222 + tableIndex) + "_" + str(i)
                parameter = self.device.getOrCreatePelTecParameter(name)
                parameter.set_update_callback(self.update_callback, "table")

    def getValue(self, tableIndex, dayIndex, i):
        name = "PVAL_" + str(222 + tableIndex) + "_" + str(dayIndex * 6 + i)
        parameter = self.device.getOrCreatePelTecParameter(name)
        if "value" in parameter.keys():
            value = parameter["value"]
            return int(value)
        return 0

    def formatTime(self, val):
        return "%02d:%02d" % (int(val / 60), val % 60)

    def getRange(self, tableIndex, dayIndex, i, j):
        val1 = self.getValue(tableIndex, dayIndex, i)
        val2 = self.getValue(tableIndex, dayIndex, j)
        if val1 == 1440 and val2 == 1440:
            return " - "
        return self.formatTime(val1) + "-" + self.formatTime(val2)

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        attributes = super().device_state_attributes
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        tables = [1, 2, 3]
        for tableIndex in tables:
            for i in range(0, 7):
                day = days[i]
                texts = [
                    self.getRange(tableIndex, i, 0, 1),
                    self.getRange(tableIndex, i, 2, 3),
                    self.getRange(tableIndex, i, 4, 5),
                ]
                key = "Table" + str(tableIndex) + " " + day
                attributes[key] = " / ".join(texts)
        return attributes

    def createEntities(hass, device) -> List[SensorEntity]:
        entities = []
        entities.append(
            PelTecWorkingTableSensor(
                hass,
                device,
                ["", "mdi:state-machine", None, "Working table"],
                device.getOrCreatePelTecParameter("PVAL_222_0"),
            )
        )
        return entities
