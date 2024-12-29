import json

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

file_path = 'test/response_14d.json'
#file_path = 'test/response_18m.json'
with open(file_path, encoding="utf8") as f:
    d = json.load(f)
    #print(d)

result = recursively_flatten_list(recursively_get_glucoseinfos(d,'glucoseInfos'))
print(result)
print(type(result))
print(len(result))