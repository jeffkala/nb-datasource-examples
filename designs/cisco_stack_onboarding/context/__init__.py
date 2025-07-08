"""Context file for Cisco Stack Onboarding."""

import logging

from nautobot_design_builder.context import Context

# from nautobot_golden_config.models import GoldenConfig
# from nautobot_plugin_nornir.constants import NORNIR_SETTINGS
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory

# from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister

from nautobot.dcim.models import Device  # , Platform

# from nornir_nautobot.exceptions import NornirNautobotException
# from nornir_nautobot.plugins.tasks.dispatcher import dispatcher


InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)

LOGGER = logging.getLogger(__name__)


def merge_switch_data(inventory_list, switch_status_list):
    switch_status_map = {item["switch"]: item for item in switch_status_list}
    for swid in switch_status_map:
        for item in inventory_list:
            merged_item = item.copy()
            if item["name"] == f"Switch {swid}" or item["name"] == swid:
                switch_status_map[swid].update(merged_item)
    return switch_status_map


class CiscoStackDesignContext(Context):
    """Render context for ipam site design."""

    def get_master_data(self, hostname):
        return Device.objects.get(name=hostname)

    def get_current_stack_master(self, stack_data):
        """Get the current stack master from the stack data."""
        for main_switch, stack_info in stack_data.items():
            for swid, swdata in stack_info.items():
                if swdata["role"] in ["Active", "Master"]:
                    current_master = f"{main_switch}:{swid}"
                    if ":1" in current_master:
                        return main_switch
                    return current_master
        return ""

    def _get_stack_data(self):
        """Static Stack Data for Testing."""
        return [
            {
                "CARVESL6-C3850": {
                    "1": {
                        "switch": "1",
                        "role": "Active",
                        "mac_address": "00f8.2c68.1f80",
                        "priority": "1",
                        "version": "V08",
                        "state": "Ready",
                        "status1": "DOWN",
                        "status2": "DOWN",
                        "neighbor1": "None",
                        "neighbor2": "None",
                        "name": "Switch 1",
                        "descr": "WS-C3850-24P-S",
                        "pid": "WS-C3850-24P-S",
                        "vid": "V08 ",
                        "sn": "FCW2005D0C9",
                    }
                }
            },
            {
                "FR-NOR-GONFR-SL039": {
                    "1": {
                        "switch": "1",
                        "role": "Active",
                        "mac_address": "d4eb.6823.d500",
                        "priority": "1",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "DOWN",
                        "status2": "DOWN",
                        "neighbor1": "None",
                        "neighbor2": "None",
                        "name": "Switch 1",
                        "descr": "C9200-24P",
                        "pid": "C9200-24P",
                        "vid": "V02 ",
                        "sn": "JAE253809YF",
                    }
                }
            },
            {
                "HOU150C9KC_NN7": {
                    "1": {
                        "switch": "1",
                        "role": "Member",
                        "mac_address": "00bc.60a6.f800",
                        "priority": "15",
                        "version": "V01",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "DOWN",
                        "neighbor1": "2",
                        "neighbor2": "None",
                        "name": "Switch 1",
                        "descr": "C9300-24U",
                        "pid": "C9300-24U",
                        "vid": "V01 ",
                        "sn": "FCW2220G0JP",
                    },
                    "2": {
                        "switch": "2",
                        "role": "Active",
                        "mac_address": "00bc.60a6.f900",
                        "priority": "1",
                        "version": "V01",
                        "state": "Ready",
                        "status1": "DOWN",
                        "status2": "OK",
                        "neighbor1": "None",
                        "neighbor2": "1",
                        "name": "Switch 2",
                        "descr": "C9300-24U",
                        "pid": "C9300-24U",
                        "vid": "V01 ",
                        "sn": "FCW2220L0KE",
                    },
                }
            },
            {
                "PASMSSWA-CK2": {
                    "1": {
                        "switch": "1",
                        "role": "Member",
                        "mac_address": "0041.d2d9.5500",
                        "priority": "15",
                        "version": "4",
                        "state": "Ready",
                        "status1": "Ok",
                        "status2": "Ok",
                        "neighbor1": "2",
                        "neighbor2": "2",
                        "name": "1",
                        "descr": "WS-C2960X-48FPS-L",
                        "pid": "WS-C2960X-48FPS-L",
                        "vid": "V02 ",
                        "sn": "FOC1945S4CD",
                    },
                    "2": {
                        "switch": "2",
                        "role": "Master",
                        "mac_address": "0041.d2d9.a180",
                        "priority": "10",
                        "version": "4",
                        "state": "Ready",
                        "status1": "Ok",
                        "status2": "Ok",
                        "neighbor1": "1",
                        "neighbor2": "1",
                        "name": "2",
                        "descr": "WS-C2960X-48FPS-L",
                        "pid": "WS-C2960X-48FPS-L",
                        "vid": "V02 ",
                        "sn": "FOC1945S4BD",
                    },
                }
            },
            {
                "US-CA-MDW-SL02": {
                    "1": {
                        "switch": "1",
                        "role": "Active",
                        "mac_address": "c44d.8408.7580",
                        "priority": "15",
                        "version": "V05",
                        "state": "Ready",
                        "status1": "DOWN",
                        "status2": "DOWN",
                        "neighbor1": "None",
                        "neighbor2": "None",
                        "name": "Switch 1",
                        "descr": "C9300-48U",
                        "pid": "C9300-48U",
                        "vid": "V05 ",
                        "sn": "FJC253714L3",
                    }
                }
            },
            {
                "US-TX-HOU150DC8MS04": {
                    "1": {
                        "switch": "1",
                        "role": "Active",
                        "mac_address": "b44c.90ed.3380",
                        "priority": "1",
                        "version": "V08",
                        "state": "Ready",
                        "status1": "DOWN",
                        "status2": "DOWN",
                        "neighbor1": "None",
                        "neighbor2": "None",
                        "name": "Switch 1",
                        "descr": "C9300L-48T-4X",
                        "pid": "C9300L-48T-4X",
                        "vid": "V08 ",
                        "sn": "FVH2817L34L",
                    }
                }
            },
            {
                "WFCSL4W1": {
                    "1": {
                        "switch": "1",
                        "role": "Member",
                        "mac_address": "d4ad.bd02.5980",
                        "priority": "15",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "2",
                        "neighbor2": "6",
                        "name": "Switch 1",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326U0AY",
                    },
                    "2": {
                        "switch": "2",
                        "role": "Member",
                        "mac_address": "d4ad.bd7a.b480",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "3",
                        "neighbor2": "1",
                        "name": "Switch 2",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FCW2326G0B2",
                    },
                    "3": {
                        "switch": "3",
                        "role": "Member",
                        "mac_address": "308b.b2ce.9f00",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "4",
                        "neighbor2": "2",
                        "name": "Switch 3",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326X05K",
                    },
                    "4": {
                        "switch": "4",
                        "role": "Active",
                        "mac_address": "d4ad.bd02.6e80",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "5",
                        "neighbor2": "3",
                        "name": "Switch 4",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326U0B1",
                    },
                    "5": {
                        "switch": "5",
                        "role": "Member",
                        "mac_address": "d4ad.bd7a.b680",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "6",
                        "neighbor2": "4",
                        "name": "Switch 5",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FCW2326C0B2",
                    },
                    "6": {
                        "switch": "6",
                        "role": "Member",
                        "mac_address": "308b.b2fc.a200",
                        "priority": "10",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "1",
                        "neighbor2": "5",
                        "name": "Switch 6",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2325U11L",
                    },
                },
            },
            {
                "WFCSL5E1": {
                    "1": {
                        "switch": "1",
                        "role": "Member",
                        "mac_address": "d4ad.bd29.a880",
                        "priority": "15",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "2",
                        "neighbor2": "4",
                        "name": "Switch 1",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326W0BR",
                    },
                    "2": {
                        "switch": "2",
                        "role": "Active",
                        "mac_address": "308b.b214.e980",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "3",
                        "neighbor2": "1",
                        "name": "Switch 2",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FCW2326G0AM",
                    },
                    "3": {
                        "switch": "3",
                        "role": "Member",
                        "mac_address": "308b.b2ce.cc00",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "4",
                        "neighbor2": "2",
                        "name": "Switch 3",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326X08P",
                    },
                    "4": {
                        "switch": "4",
                        "role": "Standby",
                        "mac_address": "d4ad.bd7a.7100",
                        "priority": "10",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "1",
                        "neighbor2": "3",
                        "name": "Switch 4",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FCW2326D05D",
                    },
                }
            },
            {
                "WR29SL13": {
                    "1": {
                        "switch": "1",
                        "role": "Active",
                        "mac_address": "c4b3.6a2a.a880",
                        "priority": "1",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "DOWN",
                        "status2": "DOWN",
                        "neighbor1": "None",
                        "neighbor2": "None",
                        "name": "Switch 1",
                        "descr": "C9300-24U",
                        "pid": "C9300-24U",
                        "vid": "V02 ",
                        "sn": "FJC2317E062",
                    }
                }
            },
        ]

    def get_stack_data(self):
        """Login to device and retrieve stack information."""
        # if self.use_sample_data:
        self.job_result.log("Using sample data, skipping logging into devices.")
        return self._get_stack_data()

        # device_filter = {
        #     "platform__name": "cisco_xe",
        #     "status__name": "Deployed",
        #     "primary_ip4__isnull": False,
        # }
        # if self.devices:
        #     device_filter["id__in"] = [device.id for device in self.devices]
        # if self.region:
        #     children = self.region.descendants(include_self=True)
        #     device_filter["location__in"] = children
        # if self.locations:
        #     device_filter["location__id__in"] = list(
        #         self.locations.values_list("id", flat=True)
        #     )
        # if self.device_role:
        #     device_filter["role"] = self.device_role
        # self.filtered_devices = Device.objects.filter(**device_filter)

        # gc_obj = GoldenConfig.objects.filter(
        #     device__in=Device.objects.filter(**device_filter)
        # )

        # self.job_result.log(f"Inscope device count: {gc_obj.count()}")
        # inscope_devices = []
        # full_stack_data = []
        # for dev in gc_obj:
        #     try:
        #         if "switch 1 prov" in dev.backup_config:
        #             inscope_devices.append(dev.device.id)
        #         else:
        #             self.job_result.log(
        #                 f"Device {dev.device.name} is not a stackable switch, skipping."
        #             )
        #     except:
        #         self.job_result.log(
        #             f"Unable to query backup configuration for {dev.device.name}, skipping."
        #         )
        # try:
        #     d = Device.objects.filter(id__in=inscope_devices)
        #     with InitNornir(
        #         runner=NORNIR_SETTINGS.get("runner"),
        #         logging={"enabled": False},
        #         inventory={
        #             "plugin": "nautobot-inventory",
        #             "options": {
        #                 "credentials_class": NORNIR_SETTINGS.get("credentials"),
        #                 "params": NORNIR_SETTINGS.get("inventory_params"),
        #                 "queryset": d,
        #             },
        #         },
        #     ) as nornir_obj:
        #         for nr_host, nr_obj in nornir_obj.inventory.hosts.items():
        #             result = nornir_obj.run(
        #                 task=dispatcher,
        #                 logger=LOGGER,
        #                 method="get_commands",
        #                 obj=nr_host,
        #                 framework="netmiko",
        #                 command_list=["show inventory", "show switch detail"],
        #                 use_textfsm=True,
        #             )
        #             try:
        #                 output = result[nr_host][0].result[0].result
        #                 merged_data = merge_switch_data(
        #                     output["output"]["show inventory"],
        #                     output["output"]["show switch detail"],
        #                 )
        #                 full_stack_data.append({nr_host: merged_data})
        #                 if self.debug:
        #                     self.job_result.log(
        #                         f"Result for {nr_host}: {result[nr_host][0].result}"
        #                     )
        #                     self.job_result.log(
        #                         f"Stack data for {nr_host}: {merged_data}"
        #                     )
        #             except:
        #                 pass

        # except NornirNautobotException as err:
        #     self.job_result.log(f"{err}")
        # return full_stack_data
