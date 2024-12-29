from setup import *
import requests
import json
# import pprint
import datetime

def convert_mmoll_to_mgdl(x):
    return round(x*ns_unit_convert)

def convert_mgdl_to_mmoll(x):
    return round(x/ns_unit_convert, 1)

# return last entry date. (Slice allows searching for modal times of day across days and months.)
def get_last_entry_date(header):
    r=requests.get(ns_url+"api/v1/slice/entries/dateString/sgv/.*/.*?count=1", headers=header)
    try:
        data = r.json()
        print("Nightscout request", r.status_code , r.reason)
        if data == []:
            print("no data from Nightscout")
            return 0
        else:
            print("Last entry date:" , data[0]["date"] ,"(GMT",datetime.datetime.utcfromtimestamp(data[0]["date"]/1000),")")
            return data[0]["date"]
    except requests.JSONDecodeError:
        content_type = r.headers.get('Content-Type')
        print("Failed. Content Type " + content_type)

# process Sisensing data
def get_ss_entries(header):
    r=requests.get(ss_url, headers=ss_header)
    try:
        data = r.json()
        print("Sisensing Response Status:" , r.status_code , r.reason)
        #pprint.pprint(r.json(), compact=True)

        # Verify response json
        print("Sisensing Json Code:", data["code"], data["msg"])
        if data["code"] != 200:
            print("Data invalid. Check your API URL and Bearer Token.")
            quit()

    except requests.JSONDecodeError:
        content_type = r.headers.get('Content-Type')
        print("Failed. Content Type " , content_type)
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

# recursive funtion to flatten nested list
def recursively_flatten_list(x):
    if x == []:
        return x
    if isinstance(x[0], list):
        return recursively_flatten_list(x[0]) + recursively_flatten_list(x[1:])
    return x[:1] + recursively_flatten_list(x[1:])

# Proces individual glucose entry
def process_json_data_prepare_json(list_data,last_date,list_dict):
    try:
        count = 0
        for i in list_data:
            #
            if uploader_max_entries !=0 and count >= uploader_max_entries:
                break
            if i["t"]>last_date or uploader_all_data==True:
                entry_dict = {
                    "type" : "sgv",
                    "sgv" : convert_mmoll_to_mgdl(i["v"]),
                    "direction" : process_json_data_direction(i["s"]),
                    "device": ns_uploder,
                    "date" : i["t"],
                    "dateString": str(datetime.datetime.utcfromtimestamp(i["t"]/1000).isoformat(timespec='milliseconds')+"Z")
                }
                list_dict.append(entry_dict)
                count +=1
        return list_dict

    except Exception as error:
        print("Error reading glucoseInfos:", error)


def process_json_data(data,last_date):
    list_dict = []
    print("Processing data...")
    try:
        list_data = recursively_flatten_list(recursively_get_glucoseinfos(data,'glucoseInfos'))
        if len(list_data) > 0:
            list_dict = process_json_data_prepare_json(list_data,last_date,list_dict)
        else:
            print("Glucose info list empty. Set up a CGM to start.")
    except Exception as error:
        print("Error reading glucose data from response json:", error)
    # finally:
    #     print(str(count) + " entries read")

    if len(list_dict) > 0:
        print("Uploading", len(list_dict), "entry(ies)...")
        upload_json = json.loads(json.dumps(list_dict))
        upload_entry(upload_json,ns_header,len(list_dict))
    elif len(list_dict) == 0:
        print("No new entry found.")
    

def upload_entry(entries_json,header,n): #entries tpye = a list of dicts
    r=requests.post(ns_url+"api/v1/entries", headers = header, json = entries_json)
    if r.status_code == 200:
        print("Nightscout POST request", r.status_code , r.reason)
        print(n, "entry(ies) uploaded.")
    else:
        print("Nightscout POST request", r.status_code , r.reason, r.text)

# return query entry date. (Slice allows searching for modal times of day across days and months.)
def get_query_entry_date(query_date,header):
    r=requests.get(ns_url+"/api/v1/slice/entries/dateString/sgv/"+query_date+".*", headers=header)
    try:
        data = r.json()
        print("Nightscout request", r.status_code , r.reason)
        print("Last entry date" , data[0]["date"] ,"GMT",datetime.datetime.utcfromtimestamp(data[0]["date"]/1000))
    except requests.JSONDecodeError:
        content_type = r.headers.get('Content-Type')
        print("Failed. Content Type " + content_type)
    return data[0]["date"]

