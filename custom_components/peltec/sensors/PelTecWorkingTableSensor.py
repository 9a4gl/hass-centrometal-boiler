import collections

from typing import List
from homeassistant.components.sensor import SensorEntity

from .PelTecGenericSensor import PelTecGenericSensor
from peltec.PelTecDeviceCollection import PelTecParameter


class PelTecWorkingTableSensor(PelTecGenericSensor):
    def __init__(self, hass, device, sensor_data, param_status, param_tables):
        super().__init__(hass, device, sensor_data, param_status)
        self.param_tables = param_tables
        for key in self.param_tables:
            for val in self.param_tables[key]:
                name = f"PVAL_{key}_{val}"
                parameter = self.device.getPelTecParameter(name)
                parameter["used"] = True

    def __del__(self):
        self.set_callback_to_all_table_parameters(None)

    def set_callback_to_all_table_parameters(self, callback):
        for key in self.param_tables:
            for val in self.param_tables[key]:
                name = f"PVAL_{key}_{val}"
                parameter = self.device.getPelTecParameter(name)
                parameter.set_update_callback(callback, f"table_{key}")

    async def async_added_to_hass(self):
        """Subscribe to sensor events."""
        await super().async_added_to_hass()
        self.set_callback_to_all_table_parameters(self.update_callback)

    def getValue(self, table_key, dayIndex, i):
        name = "PVAL_" + table_key + "_" + str(dayIndex * 6 + i)
        parameter = self.device.getPelTecParameter(name)
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
        tableIndex = 1
        for key in self.param_tables:
            for i in range(0, 7):  # iterate over days
                day = days[i]
                texts = [
                    self.getRange(key, i, 0, 1),
                    self.getRange(key, i, 2, 3),
                    self.getRange(key, i, 4, 5),
                ]
                attributes["Table" + str(tableIndex) + " " + day] = " / ".join(texts)
        return attributes

    @staticmethod
    def get_pval_data(device):
        pval = {}
        for key in device["parameters"].keys():
            if key.startswith("PVAL_"):
                data = key[5:].split("_")
                if len(data) == 2:
                    if data[0] not in pval:
                        pval[data[0]] = []
                    pval[data[0]].append(data[1])
                    pval[data[0]].sort(key=int)
        return collections.OrderedDict(sorted(pval.items()))

    @staticmethod
    def createEntities(hass, device) -> List[SensorEntity]:
        pval_data = PelTecWorkingTableSensor.get_pval_data(device)
        entities = []
        for key in pval_data.keys():
            value = pval_data[key]
            if len(value) == 42:
                parameter = PelTecParameter()
                parameter["name"] = "Table " + key
                parameter["value"] = "See attributes"
                entities.append(
                    PelTecWorkingTableSensor(
                        hass,
                        device,
                        ["", "mdi:state-machine", None, "Table " + key],
                        parameter,
                        {key: value},
                    )
                )
        return entities
