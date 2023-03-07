import collections

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor
from centrometal_web_boiler.WebBoilerDeviceCollection import WebBoilerParameter


class WebBoilerWorkingTableSensor(WebBoilerGenericSensor):
    def __init__(
        self, hass: HomeAssistant, device, sensor_data, param_status, param_tables
    ) -> None:
        super().__init__(hass, device, sensor_data, param_status)
        self.param_tables = param_tables
        for key in self.param_tables:
            for val in self.param_tables[key]:
                name = f"PVAL_{key}_{val}"
                parameter = self.device.get_parameter(name)
                parameter["used"] = True

    def __del__(self):
        self.set_callback_to_all_table_parameters(None)

    def set_callback_to_all_table_parameters(self, callback):
        for key in self.param_tables:
            for val in self.param_tables[key]:
                name = f"PVAL_{key}_{val}"
                parameter = self.device.get_parameter(name)
                parameter.set_update_callback(callback, f"table_{key}")

    async def async_added_to_hass(self):
        """Subscribe to sensor events."""
        await super().async_added_to_hass()
        self.set_callback_to_all_table_parameters(self.update_callback)

    def getValue(self, table_key, dayIndex, i):
        name = "PVAL_" + table_key + "_" + str(dayIndex * 6 + i)
        parameter = self.device.get_parameter(name)
        if "value" in parameter.keys():
            value = parameter["value"]
            return int(value)
        return 0

    def format_time(self, val):
        return "%02d:%02d" % (int(val / 60), val % 60)

    def get_range(self, tableIndex, dayIndex, i, j):
        val1 = self.getValue(tableIndex, dayIndex, i)
        val2 = self.getValue(tableIndex, dayIndex, j)
        if val1 == 1440 and val2 == 1440:
            return " - "
        return self.format_time(val1) + "-" + self.format_time(val2)

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
                    self.get_range(key, i, 0, 1),
                    self.get_range(key, i, 2, 3),
                    self.get_range(key, i, 4, 5),
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
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        pval_data = WebBoilerWorkingTableSensor.get_pval_data(device)
        entities = []
        for key in pval_data.keys():
            value = pval_data[key]
            if len(value) == 42:
                parameter = WebBoilerParameter()
                parameter["name"] = "Table " + key
                parameter["value"] = "See attributes"
                entities.append(
                    WebBoilerWorkingTableSensor(
                        hass,
                        device,
                        ["", "mdi:state-machine", None, "Table " + key],
                        parameter,
                        {key: value},
                    )
                )
        return entities
