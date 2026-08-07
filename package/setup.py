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

uploader_interval = env_int('uploader_interval', 5)
uploader_max_entries = env_int('uploader_max_entries', 0)
uploader_all_data = env_bool('uploader_all_data', False)
uploader_sensorstart = env_bool('uploader_sensorstart', False)

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
