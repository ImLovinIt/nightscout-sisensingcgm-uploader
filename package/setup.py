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

# Initilisation for docker & ENV parameters overwrite
try:
    ss_url = str(os.environ['ss_url'])
except:
    sys.exit("ss_url required. Pass it as an Environment Variable.")

try:
    ss_token = str(os.environ['ss_token'])
except:
    sys.exit("ss_token required. Pass it as an Environment Variable.")

try:
    ns_url = str(os.environ['ns_url'])
except:
    sys.exit("ns_url required. Pass it as an Environment Variable.")

try:
    ns_api_secret = str(os.environ['ns_api_secret'])
except:
    sys.exit("ns_api_secret required. Pass it as an Environment Variable.")

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
    retries = 10

try:
    timeout = int(os.environ['timeout'])
except:
    timeout = 10

try:
    if os.environ['uploader_sensorstart'].lower() == "true":
        uploader_sensorstart = True
    else:
        uploader_sensorstart = False
except:
    uploader_sensorstart = False

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