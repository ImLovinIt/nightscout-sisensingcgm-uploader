import json
import sys

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

# recursive funtion to flatten nested list. May need to increase recursion depth to avoid error.
# def recursively_flatten_list(x):
#     if x == []:
#         return x
#     if isinstance(x[0], list):
#         return recursively_flatten_list(x[0]) + recursively_flatten_list(x[1:])
#     return x[:1] + recursively_flatten_list(x[1:])

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


# change system recursion limit
# print(sys.getrecursionlimit())
# sys.setrecursionlimit(2000)

#file_path = 'test/response_14d.json'
file_path = 'test/response_14d_max_recursion.json'
#file_path = 'test/response_18m_expired_sensor.json'
#file_path = 'test/response_18m.json'

with open(file_path, encoding="utf8") as f:
    d = json.load(f)
    #print(d)
result = recursively_get_glucoseinfos(d,'glucoseInfos')
#print(result)
result = flatten_list(result)
print(result)
print(type(result))
print(len(result))
