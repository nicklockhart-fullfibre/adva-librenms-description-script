import getpass
import re
import os
import requests
import sys
import logging
import helpers
from ncclient import manager
from lxml import etree

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

LNMS_HOST = input("Please enter your LibreNMS host (e.g 'http://127.0.0.1'): ")
LNMS_API_KEY = getpass.getpass("Please paste in your LibreNMS API key: ")

SESSION = requests.session()
SESSION.headers = {"X-Auth-Token": LNMS_API_KEY}
API_ROOT = f"{LNMS_HOST}/api/v0"

# host_id = input("Enter host ID: ")
host_id = 154

host_info = SESSION.get(f"{API_ROOT}/devices/{host_id}").json()["devices"][0]

pretty_name = host_info["sysName"]
hostname = host_info["hostname"]

print(f"Found the following host: {pretty_name} ({hostname})")
if host_info["os"] != "adva_aos":
    print("Sorry, this is not an Adva device.")
    sys.exit(1)
else:
    print("This is an Adva device!")

# Get device ports
ports = SESSION.get(
    f"{API_ROOT}/devices/{host_id}/ports",
    params={'columns': 'ifName,ifAlias,port_id'}    
).json()["ports"]

# Get configuration info for the device
SSH_USER = input("Enter SSH username for NETCONF: ")
SSH_PASS = getpass.getpass("Enter SSH password for NETCONF: ")

with manager.connect(host=hostname, username=SSH_USER, password=SSH_PASS, hostkey_verify=False) as man:
    netconf_data = man.get_config(
        source="running", 
        filter=("subtree", helpers.NETCONF_SUBTREE)
    ).data[0] # root element is a list

no_change = []
updated_ports = []

for interface in netconf_data:
    name = interface.findtext(
        "acor-fac:name",
        namespaces=helpers.NETCONF_NAMESPACE
    )
    if name == None:
        # TODO why does Adva give a port with no name?
        continue

    port = helpers.get_port_by_name(ports, name)

    if not port:
        # no port by that name, try looking for its eth port
        port = helpers.get_port_eth(ports, name)

    if not port:
        # last ditch attempt, fuzzy match
        # if only one hit, probably OK... TODO confirm this behaviour
        port_candidates = helpers.get_port_by_partial_name(ports, name)
        if len(port_candidates) == 1:
            port = port_candidates[0]
            logging.warning(f"Used fuzzy matching on port {name}, got port {port['ifName']}")
        elif len(port_candidates) == 0:
            logging.warning(f"Port {name} is not known by LibreNMS!")

    if port:
        port_id = port["port_id"]
        if_alias = port["ifAlias"]
        if_name = port["ifName"]
        for tag in interface:
            if "-interface" in tag.tag:
                user_label: str = tag.findtext(
                    "acor-fac:user-label", 
                    namespaces=helpers.NETCONF_NAMESPACE
                )
                user_label = user_label.strip() # remove leading/trailing whitespace

                if not user_label:
                    # Empty label (don't do anything)
                    pass
                elif user_label == if_alias:
                    # Alias already accurate
                    no_change.append(
                        {
                            "port_id": port_id,
                            "port_name": if_name,
                            "port_label": user_label
                        }
                    )
                else:
                    # Alias has changed, mark for update
                    updated_ports.append(
                        {
                            "port_id": port_id,
                            "port_name": if_name,
                            "old_label": if_alias,
                            "new_label": user_label
                        }
                    )
    else:
        # no direct match, try vague match
        port_candidates = helpers.get_port_by_partial_name(ports, name)
        if len(port_candidates) > 0:
            print(f"Port {name} not found, but may be one of the following: {[c['ifName'] for c in port_candidates]}")


if len(no_change) > 0:
    print("The following ports would NOT be updated:")
    for port in no_change:
        print(f"\tPort name: {port['port_name']} (ID: {port['port_id']})")
        print(f"\t\tPort description: {port['port_label']}")

if len(updated_ports) > 0:
    print("The following ports WOULD be updated:")
    for port in updated_ports:
        print(f"\tPort name: {port['port_name']} (ID: {port['port_id']})")
        print(f"\t\tOld port description: {port['old_label']}")
        print(f"\t\tNew port description: {port['new_label']}")