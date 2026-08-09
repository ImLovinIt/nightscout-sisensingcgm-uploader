from setup import *
import urllib3
import urllib.parse
import json
import datetime

def convert_mmoll_to_mgdl(x):
    return round(x*ns_unit_convert)

def convert_mgdl_to_mmoll(x):
    return round(x/ns_unit_convert, 1)

# utcfromtimestamp is deprecated from Python 3.12, so build an aware UTC
# datetime instead. Nightscout wants a "Z" suffix rather than "+00:00".
def to_utc_datetime(epoch_ms):
    return datetime.datetime.fromtimestamp(epoch_ms/1000, datetime.timezone.utc)

def to_ns_datestring(epoch_ms):
    return to_utc_datetime(epoch_ms).isoformat(timespec='milliseconds').replace("+00:00", "Z")

# Nightscout rewrites created_at to its own ISO string when it stores a treatment,
# so read it back through a parser rather than string comparing what we posted.
def from_ns_datestring(value):
    try:
        parsed = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return round(parsed.timestamp()*1000)

# return last entry date. (Slice allows searching for modal times of day across days and months.)
# Returns an epoch in milliseconds, or None if the response could not be read.
def get_last_entry_date(header):
    url = ns_url+"api/v1/slice/entries/dateString/sgv/.*/.*?count=1"
    r = urllib3.request("GET", url=url,headers=header, retries=retries, timeout=timeout)
    # print(r.status,r.reason,json.loads(r.data))
    try:
        data = json.loads(r.data)
    except json.JSONDecodeError:
        print("Nightscout response was not JSON.", r.status, r.reason,
              "Content Type", r.headers.get('Content-Type'))
        return None

    print("Nightscout get last entry date:", r.status , r.reason)
    if data == []:
        print("Last entry date: no data")
        return 0
    else:
        print("Last entry date:", data[0]["date"] ,"(", to_utc_datetime(data[0]["date"]), ")")
        return data[0]["date"]

# process Sisensing data
# Returns the parsed response, or None if it was unusable. Returning None keeps
# the scheduler alive so a bad response only costs one run.
def get_ss_entries(header):
    r = urllib3.request("GET", url=ss_url,headers=header, retries=retries, timeout=timeout)
    try:
        data = json.loads(r.data)
    except json.JSONDecodeError:
        print("Sisensing response was not JSON.", r.status, r.reason,
              "Content Type", r.headers.get('Content-Type'))
        return None

    print("Sisensing Response Status:" , r.status, r.reason)

    # Verify response json
    print("Sisensing Json Code:", data.get("code"), data.get("msg"))
    if data.get("code") != 200:
        print("Data invalid. Check your API URL and Bearer Token.")
        return None
    return data

def process_json_data_direction(i):
    try:
        match i:
            case -2:
                return 'SingleDown'
            case -1:
                return 'FortyFiveDown'
            case 0:
                return 'Flat'
            case 1:
                return 'FortyFiveUp'
            case 2:
                return 'SingleUp'
    except Exception as error:
        print("Error reading direction:", error)

# example of json to Nightscout
# {
#  "type": "sgv",
#  "sgv": 146,
#  "direction": "Flat",
#  "device": "Test-Uploader",
#  "date": 1725247634000,
#  "dateString": "2024-09-02T03:27:14.000Z"
# }

# recursive function to find glucoseInfos
def recursively_get_glucoseinfos(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.items():

        if key == field:
            fields_found.append(value)

        elif isinstance(value, dict):
            results = recursively_get_glucoseinfos(value, field)
            for result in results:
                fields_found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = recursively_get_glucoseinfos(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)
    return fields_found

# The 14 day API nests the device under data.glucoseDataList[], the 18 month one
# under data.followedDeviceGlucoseDataPO, so find the block by a key it always
# carries instead of hard coding either path. Descending stops at the block, so
# the thousands of readings inside it are never walked.
def recursively_get_device_blocks(search_dict):
    if "deviceEnableTime" in search_dict:
        return [search_dict]

    blocks_found = []

    for value in search_dict.values():

        if isinstance(value, dict):
            for result in recursively_get_device_blocks(value):
                blocks_found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for another_result in recursively_get_device_blocks(item):
                        blocks_found.append(another_result)
    return blocks_found

# recursive funtion to flatten nested list. NOT IN USE due to max recursion depth error.
def recursively_flatten_list(x):
    if x == []:
        return x
    if isinstance(x[0], list):
        return recursively_flatten_list(x[0]) + recursively_flatten_list(x[1:])
    return x[:1] + recursively_flatten_list(x[1:])

# flatten list, assuming Sisensing won't have nested glucoseInfos list.
def flatten_list(x):
    result = []
    if x == []:
        return x
    for i in x:
        if isinstance(i, list):
            for j in i:
                result.append(j)
        else:
            result.append(i)
    return result

# Proces individual glucose entry
# Catches per entry so one malformed reading does not discard the whole batch.
def process_json_data_prepare_entries(list_data,last_date,list_dict):
    count = 0
    for i in list_data:
        if uploader_max_entries !=0 and count >= uploader_max_entries:
            break
        try:
            if i["t"]>last_date or uploader_all_data==True:
                entry_dict = {
                    "type" : "sgv",
                    "sgv" : convert_mmoll_to_mgdl(i["v"]),
                    "direction" : process_json_data_direction(i["s"]),
                    "device": ns_uploder,
                    "date" : i["t"],
                    "dateString": to_ns_datestring(i["t"])
                }
                list_dict.append(entry_dict)
                count +=1
        except Exception as error:
            print("Error reading glucoseInfos entry:", error)
    return list_dict


def process_json_data(data,last_date):
    list_dict = []
    print("Processing data...")
    try:
        list_data = flatten_list(recursively_get_glucoseinfos(data,'glucoseInfos'))
        if len(list_data) > 0:
            process_json_data_prepare_entries(list_data,last_date,list_dict)
        else:
            print("Glucose info list empty. Set up a CGM to start.")
    except Exception as error:
        print("Error reading glucose data from response json:", error)
    # finally:
    #     print(str(count) + " entries read")

    if len(list_dict) > 0:
        print("Uploading", len(list_dict), "entry(ies)...")
        upload_entry(list_dict,ns_header,len(list_dict))
    else:
        print("No new entry found.")


def upload_entry(entries_json,header,n): #entries tpye = a list of dicts
    url = ns_url+"api/v1/entries"
    r = urllib3.request("POST", url=url,headers=header, json = entries_json, retries=retries, timeout=timeout)
    if r.status == 200:
        print("Nightscout POST entries:", r.status, r.reason)
        print(n, "entry(ies) uploaded.")
    else:
        print("POST Failed.", r.status, r.reason, r.data[:500])

# Nightscout treatments. Gated by uploader_sensor_events, off by default.
# get the most recent treatment of one eventType posted by this uploader.
# Nightscout sorts treatments by created_at descending by default, so count=1
# returns the latest. Returns the treatment dict, or None if there is not one.
def get_last_treatment(header,event_type):
    # Nightscout constrains any query carrying no date clause to the last four days
    # (lib/server/query.js, deltaAgo = TWO_DAYS * 2). A sensor start is up to 14 days
    # old, so without this the lookup returns nothing and the treatment is re-posted
    # on every run.
    query = urllib.parse.urlencode({"count": 1,
                                    "find[eventType]": event_type,
                                    "find[enteredBy]": ns_uploder,
                                    "find[created_at][$gte]": "1970",
                                    })
    url = ns_url+"api/v1/treatments.json?"+query
    r = urllib3.request("GET", url=url,headers=header, retries=retries, timeout=timeout)
    try:
        data = json.loads(r.data)
    except json.JSONDecodeError:
        print("Nightscout response was not JSON.", r.status, r.reason,
              "Content Type", r.headers.get('Content-Type'))
        return None

    print("Nightscout get last", event_type+":", r.status , r.reason)
    if not isinstance(data, list) or data == []:
        print("Last", event_type+": no data")
        return None
    else:
        print("Last", event_type+":", data[0].get("created_at"))
        return data[0]

# deviceEnableTime claims to be the activation and is in SECONDS, unlike every
# other timestamp in the response, but it is skewed and cannot be used as an event
# time. In sample_json/response_14d.json it sits 3h 1m after the sensor really
# started; a live 2026-08-09 session put it 2h 1m after, an hour that is exactly
# the AEDT to AEST change. The gap tracks the local UTC offset minus 8 hours, so
# the field reads like a wall clock rendered in UTC+8 rather than a true epoch.
#
# Every reading instead carries "i", a minute index counted from activation, so
# t - i*60000 recovers the real start from any reading with no timezone involved.
# Readings disagree by up to a minute, so take the median rather than an edge:
# in the 502 reading sample the median lands on the value 370 of them agree on.
def sensor_activation_from_readings(device):
    bases = []
    for reading in flatten_list(recursively_get_glucoseinfos(device,'glucoseInfos')):
        try:
            bases.append(int(reading["t"]) - int(reading["i"])*60000)
        except (TypeError, ValueError, KeyError):
            continue
    if len(bases) == 0:
        return None
    bases.sort()
    return bases[len(bases)//2]

# deviceLastTime is activation plus 14 days, a schedule rather than an observation,
# so it is not used as an event time either.
def prepare_treatment_sensorstart(device):
    start_date = sensor_activation_from_readings(device)
    if start_date is None:
        print("No glucose reading carries an index. Skipping Sensor Start.")
        return None
    return {
        "eventType": "Sensor Start",
        "created_at": to_ns_datestring(start_date),
        "notes": "Sisensing "+str(device.get("deviceName")),
        "enteredBy": ns_uploder,
    }

# The response carries no stop time. Once a sensor ends, deviceStatus leaves 1 and
# glucoseInfos empties, but latestGlucoseTime keeps the final reading, so that is
# the stop. Readings can run hours past deviceLastTime, so the scheduled end is
# not a substitute for it.
def prepare_treatment_sensorstop(device):
    status = device.get("deviceStatus")
    if status is None or status == 1:
        return None
    if not device.get("latestGlucoseTime"):
        print("Sensor is not running but the response has no usable stop time.")
        return None

    stop_date = int(device["latestGlucoseTime"])
    # An expired sensor empties glucoseInfos, so the index is usually gone by the
    # time a stop is posted. Fall back to deviceEnableTime here: it is skewed by a
    # couple of hours, which is fine for a floor on a 14 day wear, and only a
    # sanity check hangs on it. Without either the floor is skipped, not the stop.
    start_date = sensor_activation_from_readings(device)
    if start_date is None and device.get("deviceEnableTime"):
        start_date = int(device["deviceEnableTime"])*1000
    # a stop at or before the activation would be a bad read, not a short wear
    if start_date is not None and stop_date <= start_date:
        print("Ignoring Sensor Stop, latestGlucoseTime is not after the activation.")
        return None

    return {
        "eventType": "Sensor Stop",
        "created_at": to_ns_datestring(stop_date),
        "notes": "Sisensing "+str(device.get("deviceName"))+", deviceStatus "+str(status),
        "enteredBy": ns_uploder,
    }

# Nightscout upserts a treatment on eventType plus created_at when no identifier is
# sent, so re-posting the same event overwrites it rather than duplicating it. The
# check below only avoids a pointless POST on every run.
def upload_treatment_if_new(treatment,header):
    if treatment is None:
        return
    last = get_last_treatment(header,treatment["eventType"])
    if last is not None and from_ns_datestring(last.get("created_at")) == from_ns_datestring(treatment["created_at"]):
        print(treatment["eventType"], "already recorded at", treatment["created_at"])
        return
    print("Uploading", treatment["eventType"], "at", treatment["created_at"], "...")
    upload_treatment([treatment],header)

def upload_treatment(treatments_json,header): #treatments type = a list of dicts
    url = ns_url+"api/v1/treatments"
    r = urllib3.request("POST", url=url,headers=header, json = treatments_json, retries=retries, timeout=timeout)
    if r.status == 200:
        print("Nightscout POST treatments:", r.status, r.reason)
    else:
        print("POST Failed.", r.status, r.reason, r.data[:500])

def process_sensor_events(data,header):
    print("Processing sensor events...")
    try:
        devices = recursively_get_device_blocks(data)
    except Exception as error:
        print("Error reading device data from response json:", error)
        return

    if len(devices) == 0:
        print("No device found in response. Set up a CGM to start.")
        return
    if len(devices) > 1:
        print("Response holds", len(devices), "devices. Using the first.")

    device = devices[0]
    for prepare in (prepare_treatment_sensorstart, prepare_treatment_sensorstop):
        try:
            upload_treatment_if_new(prepare(device),header)
        except Exception as error:
            print("Error processing sensor event:", error)
