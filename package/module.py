from setup import *
import requests
import json
import pprint
import datetime

def return_ss_url(ss_region):
    match ss_region:
        case "CN":
            return region_cn
        # EU to be tested
        case "EU":
            return region_eu

def convert_mmoll_to_mgdl(x):
    return round(x*ns_unit_convert)

def convert_mgdl_to_mmoll(x):
    return round(x/ns_unit_convert, 1)

# return last entry date. (Slice allows searching for modal times of day across days and months.)
def get_last_entry_date(header):
    r=requests.get(ns_url+"api/v1/slice/entries/dateString/sgv/.*/.*?count=1", headers=header, timeout=5)
    try:
        data = r.json()
        print("Nightscout request", r.status_code , r.reason)
        if data == []:
            print("no data")
            return 0
        else:
            print("Last entry date:" , data[0]["date"] ,"(GMT",datetime.datetime.utcfromtimestamp(data[0]["date"]/1000),")")
            return data[0]["date"]
    except requests.JSONDecodeError:
        content_type = r.headers.get('Content-Type')
        print("Failed. Content Type " + content_type)

# process Sisensing data
def get_ss_entries(header):
    r=requests.get(return_ss_url(ss_region.upper()), headers=ss_header, timeout=5)
    try:
        data = r.json()
        print("Sisensing Response Status:" , r.status_code , r.reason)
        #pprint.pprint(r.json(), compact=True)
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

# ADD CODE FOR MISSING DATA
def process_json_data_prepare_json(item,last_date,count,list_dict): # item type = dict
    try:
        for j in item["glucoseInfos"]:
            #
            if uploader_max_entries !=0 and count >= uploader_max_entries:
                break
            if j["t"]>last_date or uploader_all_data==True:
                entry_dict = {
                    "type" : "sgv",
                    "sgv" : convert_mmoll_to_mgdl(j["v"]),
                    "direction" : process_json_data_direction(j["s"]),
                    "device": ns_uploder,
                    "date" : j["t"],
                    "dateString": str(datetime.datetime.utcfromtimestamp(j["t"]/1000).isoformat(timespec='milliseconds')+"Z")
                }
                list_dict.append(entry_dict)
                count +=1
        return count,list_dict
    except Exception as error:
        print("Error reading glucoseInfos:", error)


def process_json_data(data,last_date):
    count = 0
    list_dict = []
    print("Processing data...")
    try:
        if type(data["data"]["glucoseDataList"]) == list:
            for i in data["data"]["glucoseDataList"]:
                count,list_dict = process_json_data_prepare_json(i,last_date,count,list_dict)
        elif type(data["data"]["glucoseDataList"]) == dict:
            count,list_dict = process_json_data_prepare_json(i,last_date,count,list_dict)
        else:
            print(type(data["data"]["glucoseDataList"]), " recieved. Check API content.")
    except Exception as error:
        print("Error reading glucose data:", error)
    # finally:
    #     print(str(count) + " entries read")

    if len(list_dict) > 0:
        upload_json = json.loads(json.dumps(list_dict))
        upload_entry(upload_json,ns_header,len(list_dict))
    else:
        print("No new entry found.")
    

def upload_entry(entries_json,header,n): #entries tpye = a list of dicts
    r=requests.post(ns_url+"api/v1/entries", headers = header, json = entries_json, timeout=5)
    if r.status_code == 200:
        print("Nightscout POST request", r.status_code , r.reason)
        print(n, "entries uploaded.")
    else:
        print("Nightscout POST request", r.status_code , r.reason, r.text)

# return query entry date. (Slice allows searching for modal times of day across days and months.)
def get_query_entry_date(query_date,header):
    r=requests.get(ns_url+"/api/v1/slice/entries/dateString/sgv/"+query_date+".*", headers=header, timeout=5)
    try:
        data = r.json()
        print("Nightscout request", r.status_code , r.reason)
        print("Last entry date" , data[0]["date"] ,"GMT",datetime.datetime.utcfromtimestamp(data[0]["date"]/1000))
    except requests.JSONDecodeError:
        content_type = r.headers.get('Content-Type')
        print("Failed. Content Type " + content_type)
    return data[0]["date"]

