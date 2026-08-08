import os
import sys
# import docker

# Initilisation for local python script
# ss_url = ""
# ss_token = ""
# ns_url = ""
# ns_api_secret= "" #api_secret
# uploader_interval = 5 #mins
# uploader_max_entries = 0 # 0 to disable.
# uploader_all_data = False
# retries = 10
# timeout = 10

# Environment variable readers.
# A bare "except" here would also swallow KeyboardInterrupt and SystemExit, and
# str/int/bool each need different handling, so read them explicitly instead.
def env_str(name, default=None, required=False):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        if required:
            sys.exit(name + " required. Pass it as an Environment Variable.")
        return default
    return value


def env_int(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        sys.exit(name + " must be a whole number. Got: " + value)


def env_bool(name, default=False):
    # bool("False") is True, so the string has to be compared, not cast.
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("true", "1", "yes", "on")


# Initilisation for docker & ENV parameters overwrite
ss_url = env_str('ss_url', required=True)
ss_token = env_str('ss_token', required=True)
ns_url = env_str('ns_url', required=True)
ns_api_secret = env_str('ns_api_secret', required=True)

# Every Nightscout call concatenates a path straight onto ns_url, so a missing
# trailing slash turns https://host + api/v1/entries into https://hostapi/v1/entries
# and the whole run fails on DNS. Guarantee the separator here instead of trusting
# the variable, and strip stray whitespace while at it.
ns_url = ns_url.strip().rstrip("/")+"/"
# ss_url is sent exactly as captured and never has a path appended, so it is left
# alone. The two documented endpoints differ on the trailing slash.
ss_url = ss_url.strip()

# urllib3 cannot request a schemeless URL, and the failure it raises is not obvious,
# so say so plainly at startup.
# underscore names so "from setup import *" does not export the loop variables
for _name, _value in (("ns_url", ns_url), ("ss_url", ss_url)):
    if not _value.lower().startswith(("http://", "https://")):
        sys.exit(_name + " must start with http:// or https://. Got: " + _value)

uploader_interval = env_int('uploader_interval', 5)
uploader_max_entries = env_int('uploader_max_entries', 0)
uploader_all_data = env_bool('uploader_all_data', False)
# One switch for both Sensor Start and Sensor Stop treatments. uploader_sensorstart
# was the earlier name for this and was never wired up, so it is still accepted.
uploader_sensor_events = env_bool('uploader_sensor_events', env_bool('uploader_sensorstart', False))

retries = env_int('retries', 10)
timeout = env_int('timeout', 10)

if uploader_interval <= 0:
    sys.exit("uploader_interval must be greater than 0.")

# uploader initialisation
ns_uploder = "Nightscout-Sisensing-Uploader"
ns_unit_convert = 18.018

# header initialisation
ns_header = {"api-secret": ns_api_secret,
             "User-Agent": "Sisensing Nightscout Uploader",
             "Content-Type": "application/json",
             "Accept":"application/json",
             }

ss_header = {"Authorization":ss_token,
             "User-Agent": "Sisensing Nightscout Uploader",
             "Content-Type": "application/json",
             "Accept":"application/json",
             }
