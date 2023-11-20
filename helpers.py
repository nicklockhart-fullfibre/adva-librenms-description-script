"""
Helper functions and constants for the ADVA port description update script.
"""
import re

IS_FSP = re.compile(r"^lag-\d*$")

# FIXME TODO this is hacky, I should be following the xpath properly, but for now this'll do... hopefully
IF_NAME = re.compile(r"acor-fac:name=\"(.*)\"")

NETCONF_SUBTREE = """
<managed-element>
    <interface/>
</managed-element>
"""

NETCONF_NAMESPACE = {
    "acor-fac": "http://www.advaoptical.com/aos/netconf/aos-core-facility",
    "acor-me": "http://www.advaoptical.com/aos/netconf/aos-core-managed-element"
}

def get_port_by_name(ports: list, port_name: str) -> dict:
    "Get a port from a port name."
    for port in ports:
        if port["ifName"] == port_name:
            return port

def get_port_by_partial_name(ports: list, port_name: str) -> list:
    "Get a port based on a partial name. Returns a list of matches."
    matching_ports = []
    if port_name is not None:
        for port in ports:
            if port_name in port["ifName"]:
                matching_ports.append(port)
    return matching_ports

def get_port_eth(ports: list, port_name: str) -> dict:
    "Get a port's eth port (xyz/eth) from its name (xyz)."
    for port in ports:
        if port["ifName"] == f"{port_name}/eth":
            return port