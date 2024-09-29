import os
import sys

# Initilisation for local python script
# ss_token = ""
# ss_region = "CN"
# ns_url = ""
# ns_api_secret= "" #api_secret
# uploader_sensorstart = False
# uploader_interval = 5 #mins
# uploader_max_entries = 0 # 0 to disable.

# Initilisation for docker & ENV parameters overwrite
try:
    ss_token = str(os.environ['ss_token'])
except:
    sys.exit("ss_token required. Pass it as an Environment Variable.")

try:
    ss_region = str(os.environ['ss_region'])
except:
    ss_region = "CN"

try:
    ns_url = str(os.environ['ns_url'])
except:
    sys.exit("ns_url required. Pass it as an Environment Variable.")

try:
    ns_api_secret = str(os.environ['ns_api_secret'])
except:
    sys.exit("ns_api_secret required. Pass it as an Environment Variable.")

try:
    uploader_sensorstart = int(os.environ['uploader_sensorstart'])
except:
    uploader_sensorstart = False

try:
    uploader_interval = int(os.environ['uploader_interval'])
except:
    uploader_interval = 5

try:
    uploader_max_entries = int(os.environ['uploader_max_entries'])
except:
    uploader_max_entries = 0

try:
    uploader_all_data = bool(os.environ['uploader_all_data'])
except:
    uploader_all_data = False

try:
    retries = int(os.environ['retries'])
except:
    retries = 5

try:
    timeout = int(os.environ['timeout'])
except:
    timeout = 5

try:
    if os.environ['uploader_sensorstart'].lower() == "true":
        uploader_sensorstart = True
    else:
        uploader_sensorstart = False
except:
    uploader_sensorstart = False

#API URL
region_list = ["CN","EU"]
if ss_region.upper() not in region_list:
    sys.exit(ss_region, "not found.")
region_cn = "https://api.sisensing.com/follow/app/follow/myself/glucose/details/devices"
region_eu = "https://cgm-ce.sisensing.com/user/app/follow/sharer"

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