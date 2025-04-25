"""Context file for Cisco Stack Onboarding."""
import logging
from nautobot_design_builder.context import Context
from nautobot.dcim.models import Device, Platform
from nautobot_golden_config.models import GoldenConfig

from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_nautobot.exceptions import NornirNautobotException
from nornir_nautobot.plugins.tasks.dispatcher import dispatcher

InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)

LOGGER = logging.getLogger(__name__)

def merge_switch_data(inventory_list, switch_status_list):
    switch_status_map = {item['switch']: item for item in switch_status_list}
    for swid in switch_status_map:
        for item in inventory_list:
            merged_item = item.copy()
            if item['name'] == f"Switch {swid}" or item['name'] == swid:
                switch_status_map[swid].update(merged_item)
    return switch_status_map


class CiscoStackDesignContext(Context):
    """Render context for ipam site design."""

    def get_master_data(self, hostname):
        return Device.objects.get(name=hostname)

    # def get_stack_data(self):
    #     return [
    #         {
    #             "RL01": {
    #                 "1": {
    #                     "switch": "1",
    #                     "role": "Active",
    #                     "mac_address": "ecc0.1835.df80",
    #                     "priority": "1",
    #                     "version": "V06",
    #                     "state": "Ready",
    #                     "status1": "OK",
    #                     "status2": "OK",
    #                     "neighbor1": "2",
    #                     "neighbor2": "2",
    #                     "name": "Switch 1",
    #                     "descr": "C9300-24U",
    #                     "pid": "C9300-24U",
    #                     "vid": "V06  ",
    #                     "sn": "FOC2710Y6DL"
    #                 },
    #                 "2": {
    #                     "switch": "2",
    #                     "role": "Standby",
    #                     "mac_address": "ecc0.1843.f780",
    #                     "priority": "1",
    #                     "version": "V06",
    #                     "state": "Ready",
    #                     "status1": "OK",
    #                     "status2": "OK",
    #                     "neighbor1": "1",
    #                     "neighbor2": "1",
    #                     "name": "Switch 2",
    #                     "descr": "C9300-24U",
    #                     "pid": "C9300-24U",
    #                     "vid": "V06  ",
    #                     "sn": "FOC2710Y6HU"
    #                 }
    #             }
    #         },
    #         {
    #             "CK2": {
    #                 "1": {
    #                     "switch": "1",
    #                     "role": "Member",
    #                     "mac_address": "0041.d2d9.5500",
    #                     "priority": "15",
    #                     "version": "4",
    #                     "state": "Ready",
    #                     "status1": "Ok",
    #                     "status2": "Ok",
    #                     "neighbor1": "2",
    #                     "neighbor2": "2",
    #                     "name": "1",
    #                     "descr": "WS-C2960X-48FPS-L",
    #                     "pid": "WS-C2960X-48FPS-L",
    #                     "vid": "V02  ",
    #                     "sn": "FOC1945S4CD"
    #                 },
    #                 "2": {
    #                     "switch": "2",
    #                     "role": "Master",
    #                     "mac_address": "0041.d2d9.a180",
    #                     "priority": "10",
    #                     "version": "4",
    #                     "state": "Ready",
    #                     "status1": "Ok",
    #                     "status2": "Ok",
    #                     "neighbor1": "1",
    #                     "neighbor2": "1",
    #                     "name": "2",
    #                     "descr": "WS-C2960X-48FPS-L",
    #                     "pid": "WS-C2960X-48FPS-L",
    #                     "vid": "V02  ",
    #                     "sn": "FOC1945S4BD"
    #                 }
    #             }
    #         }
    #     ]

    def get_stack_data(self):
        """Login to device and retrieve stack information."""
        gc_obj = GoldenConfig.objects.filter(device__in=Device.objects.filter(platform__in=Platform.objects.filter(name__in=["cisco_xe", "cisco_ios"])))
        inscope_devices = []
        full_stack_data = []
        for dev in gc_obj:
            try:
                if 'switch 1 prov' in dev.backup_config:
                    inscope_devices.append(dev.device.id)
            except:
                pass
        try:
            d = Device.objects.filter(id__in=inscope_devices)
            with InitNornir(
                runner=NORNIR_SETTINGS.get("runner"),
                logging={"enabled": False},
                inventory={
                    "plugin": "nautobot-inventory",
                    "options": {
                        "credentials_class": NORNIR_SETTINGS.get("credentials"),
                        "params": NORNIR_SETTINGS.get("inventory_params"),
                        "queryset": d,
                    },
                },
            ) as nornir_obj:
                for nr_host, nr_obj in nornir_obj.inventory.hosts.items():
                    result = nornir_obj.run(
                        task=dispatcher,
                        logger=LOGGER,
                        method="get_commands",
                        obj=nr_host,
                        framework="netmiko",
                        command_list=["show inventory", "show switch detail"],
                        use_textfsm=True,
                    )
                    try:
                        output = result[nr_host][0].result[0].result
                        merged_data = merge_switch_data(output["output"]["show inventory"], output["output"]["show switch detail"])
                        full_stack_data.append({nr_host: merged_data})
                    except:
                        pass

        except NornirNautobotException as err:
            LOGGER.error(err)
        return full_stack_data
