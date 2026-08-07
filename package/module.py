from setup import *
import urllib3
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

# Nightscout treatment
# WORK IN PROGRESS. Nothing below is wired into main() yet, and the
# uploader_sensorstart flag that will gate it is currently unused.
# get last sensor start date
def get_last_treatment_sensorstart_date(header):
    url = ns_url+"api/v1/treatments.json?count=1&find[eventType]=Sensor Start&find[enteredBy]="+ns_uploder+"&find[created_at][$gte]=1970"
    r = urllib3.request("GET", url=url,headers=header, retries=retries, timeout=timeout)
    # print(r.status,r.reason,json.loads(r.data))
    try:
        data = json.loads(r.data)
    except json.JSONDecodeError:
        print("Nightscout response was not JSON.", r.status, r.reason,
              "Content Type", r.headers.get('Content-Type'))
        return None

    print("Nightscout get last sensor start date:", r.status , r.reason)
    if data == []:
        print("Last sensor date: no data")
        return "0"
    else:
        print("Last sensor date:", data[0]["created_at"])
        return data[0]["created_at"]

def process_json_data_prepare_treatment_sensorstart(item,last_date,count,list_dict): # item type = dict
    try:
        if uploader_max_entries !=0 and count >= uploader_max_entries:
            return count,list_dict
        if item["GlucoseEntryDateTime"]>last_date or uploader_all_data==True:
            entry_dict = {
                "eventType": "BG Check",
                "created_at": datetime.datetime.fromisoformat(item["GlucoseEntryDateTime"]).isoformat(timespec="milliseconds")+"Z",
                "glucose": item["GlucoseLevel"],
                "glucoseType": "Finger",
                "units": "mmol",
                "enteredBy": ns_uploder,
            }
            list_dict.append(entry_dict)
            count +=1
        return count,list_dict
    except Exception as error:
        print("Error processing BloodGlucose:", error)
        return count,list_dict
