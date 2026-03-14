import collections

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from .WebBoilerGenericSensor import WebBoilerGenericSensor
from centrometal_web_boiler.WebBoilerDeviceCollection import WebBoilerParameter


class WebBoilerWorkingTableSensor(WebBoilerGenericSensor):
    def __init__(self, hass, device, sensor_data, param_status, param_tables) -> None:
        super().__init__(hass, device, sensor_data, param_status)
        self.param_tables = param_tables
        for key in self.param_tables:
            for val in self.param_tables[key]:
                parameter = self.device.get_parameter(f"PVAL_{key}_{val}")
                parameter["used"] = True

    def __del__(self):
        super().__del__()
        self._set_callback_all(None)

    def _set_callback_all(self, callback):
        for key in self.param_tables:
            for val in self.param_tables[key]:
                parameter = self.device.get_parameter(f"PVAL_{key}_{val}")
                parameter.set_update_callback(callback, f"table_{key}")

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._set_callback_all(self.update_callback)

    def _get_slot_value(self, table_key, day_index, slot):
        parameter = self.device.get_parameter(f"PVAL_{table_key}_{day_index * 6 + slot}")
        if "value" in parameter.keys():
            return int(parameter["value"])
        return 0

    def _format_minutes(self, val):
        return "%02d:%02d" % (int(val / 60), val % 60)

    def _get_range(self, table_key, day_index, start_slot, end_slot):
        val1 = self._get_slot_value(table_key, day_index, start_slot)
        val2 = self._get_slot_value(table_key, day_index, end_slot)
        if val1 == 1440 and val2 == 1440:
            return " - "
        return self._format_minutes(val1) + "-" + self._format_minutes(val2)

    @property
    def extra_state_attributes(self):
        base = super().extra_state_attributes or {}
        attributes = dict(base)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for key in self.param_tables:
            for day_idx in range(7):
                ranges = [
                    self._get_range(key, day_idx, 0, 1),
                    self._get_range(key, day_idx, 2, 3),
                    self._get_range(key, day_idx, 4, 5),
                ]
                attributes[f"Table{key} {days[day_idx]}"] = " / ".join(ranges)
        return attributes

    @staticmethod
    def _get_pval_data(device):
        pval = {}
        for key in device["parameters"].keys():
            if key.startswith("PVAL_"):
                data = key[5:].split("_")
                if len(data) == 2:
                    if data[0] not in pval:
                        pval[data[0]] = []
                    if data[1] not in pval[data[0]]:
                        pval[data[0]].append(data[1])
                        pval[data[0]].sort(key=int)
        return collections.OrderedDict(sorted(pval.items()))

    @staticmethod
    def create_entities(hass: HomeAssistant, device) -> list[SensorEntity]:
        pval_data = WebBoilerWorkingTableSensor._get_pval_data(device)
        entities: list[SensorEntity] = []
        for key, value in pval_data.items():
            if len(value) == 42:
                parameter = WebBoilerParameter()
                parameter["name"] = "Table " + key
                parameter["value"] = "See attributes"
                entities.append(
                    WebBoilerWorkingTableSensor(
                        hass, device,
                        [None, "mdi:state-machine", None, "Table " + key],
                        parameter,
                        {key: value},
                    )
                )
        return entities
