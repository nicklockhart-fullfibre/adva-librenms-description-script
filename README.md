# adva-librenms-description-script
A Python script to pull port labels from ADVA gear over Netconf and push them into LibreNMS.
## How to Use
- Both scripts depend on `ncclient`.
- You will likely have to change `host_id` on line 36 (see TODO).
- `cli.py`: You will be asked for info and credentials as needed.
- `script.py`: You'll need some environment variables.
  - Set `LNMS_HOST` to a value like `http://127.0.0.1` (you **must** include the protocol).
  - Set `LNMS_API_KEY` to your API key.
## TODO
- Make the script iterate over a device group in LibreNMS, to bulk-update a set of FSPs instead of just one host.
  - Alternatively, make it flexible - make it work with either a host ID or group ID
- Make the script use an SSH key instead of prompting for credentials, to allow it to run in the background.
