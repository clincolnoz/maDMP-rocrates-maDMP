import copy
import json
import jsonschema
import os
import sys
import urllib
import argparse

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

    
def read_json_url(url):
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data


def read_json_local(path):
    with open(path, 'r') as in_file:
        data = json.load(in_file)
    return data


def write_json_local(path, data):
    try:
        with open(path, 'w') as out_file:
            status = json.dump(data, out_file, indent=4)
    except Exception as e:
        print('Failed to write json with error: {}'.format(e))
    

def write_rocrates(path, rocrates):
    path_root = os.path.split(path)[0]
    for i, rocrate in enumerate(rocrates):
        path_manifest = os.path.join(path_root, 'dataset_{}'.format(i))
        if not os.path.isdir(path_manifest):
            os.mkdir(path_manifest)
        write_json_local(os.path.join(path_manifest, 'manifest.jsonld'), rocrate)

        
def check_valid_dmp(dmp, schema):
    print(color.BOLD + 'Checking if valid maDMP' + color.END)
    try:
        jsonschema.validate(instance=dmp, schema=schema)
        print(color.GREEN + 'VALID' + color.END)
        valid = 1
    except Exception as e:
        valid = 0
        print(color.RED + 'NOT VALID' + color.END)
        print('with the following exceptions:\n')
        print(e)
        pass
    return valid


def get_value(d, k):
    _d = d
    if k.find('::'):
        subkeys = k.split('::')
        for subkey in subkeys[:-1]:
            if subkey in _d:
                _d = _d[subkey]
            else:
                value = -1
                break
    else:
        subkeys = k
    if subkeys[-1] in _d:    
        value = _d[subkeys[-1]]
    else:
        value = -1
    return value


def get_identifer_type_for_dmp(value):
    if not value.find('handle') == -1:
        id_type = 'handle'
    elif not value.find('orcid') == -1:
        id_type = 'orcid'
    elif not value.find('ark') == -1:
        id_type = 'ark'
    elif not value.find('isni') == -1:
        id_type = 'isni'
    elif not value.find('openid') == -1:
        id_type = 'openid'
    else:
        id_type = 'other'
    return id_type


def nested_set(dic, keys, value, create_missing=True):
    d = dic
    if keys.find('::'):
        keys = keys.split('::')
        for key in keys[:-1]:
            if key in d:
                d = d[key]
            elif create_missing:
                d = d.setdefault(key, {})
            else:
                return dic
    if keys[-1] in d or create_missing:
        d[keys[-1]] = value
        if keys[-1] == 'identifier':
            d['type'] = get_identifer_type_for_dmp(value)
            #print([value, get_identifer_type_for_dmp(value)])
            
    return dic


def parse_mapping(d, mapping):
    d_out = {}
    for k, v in mapping.items():
        if isinstance(v, dict):
            d_out = add_entry_from_value(d_out, v)
            continue
        value = get_value(d, k)
        if not value == -1:
            if isinstance(value, list):
                if isinstance(v, list):
                    if v[1] == 'list_to_str':
                        d_out[v[0]] = ', '.join(value)
                        continue
                d_out[v[0]] = parse_list(value, d, v[1])
                continue
            if isinstance(value, dict):
                d_out[v[0]] = parse_mapping(value, v[1])
                continue
            if k == 'keywords':
                value = value.split(', ')
            d_out = nested_set(d_out, v, value)
    return d_out

def parse_list(lst, d, mapping):
    lst_out = []
    for item in lst:
        if isinstance(item, dict):
            # worst hack ever to get list item from dict
            if list(mapping.values())[0] == 'list_item':
                item_out = get_value(item, list(mapping.keys())[0])
            else:
                item_out = parse_mapping(item, mapping)
        elif isinstance(mapping, dict):
            item_out = parse_value_mapping(d, item, mapping)
        else:
            item_out = item
        lst_out.append(item_out)
    return lst_out


def parse_value_mapping(d, item, mapping):
    d_out = {}
    for k, v in mapping.items():
        if isinstance(v, dict):
            for _k, _v in v.items():
                if _v == 'item':
                    d_out[_k] = item
                    continue
                d_out[_k] = _v
            continue
        value = get_value(d, k)
        if not value == -1:
            d_out[v] = value
    return d_out

def add_entry_from_value(d, value_dict):
    for k, v in value_dict.items():
        d = nested_set(d, k, v)
    return d


role_value_mapping = {
    'name': 'list_item'
}

contributor_mapping = {
    '@id':'contributor_id::identifier',
    'email': 'mbox',
    'name': 'name',
    'roleName': ['role', role_value_mapping],
}

contact_mapping = {
    '@id':'contact_id::identifier',
    'email': 'mbox',
    'name': 'name',
}

cost_mapping = {
    '@id': 'title',
    'costCurrency': 'currency_code',
    'description': 'description',
    'value': 'value',
}

funder_mapping = {
    '@id': 'grant_id::identifier',
    'funder::@id': 'funder_id::identifier',
    'description': 'funding_status',
}

project_mapping = {
    '@id': "project_id",
    "name": "title",
    #"project_id_type": "type",
    "startDate": "start",  # on top level temporalCoverage = "temporalCoverage_i/temporalCoverage_f"
    "endDate": "end",
    "description": "description",
    'funder': ["funding", funder_mapping],  # list to list
}

dmp_header_to_dataset_mapping = {
    'language': 'language',
    'dateCreated': 'created',
    'datePublished': 'modified',
    'contactPoint': ['contact', contact_mapping],
    'creator': ['contributor', contributor_mapping],
    'cost': ['cost', cost_mapping],
    'ethicsPolicy::ethical_issues_exist': 'ethical_issues_exist',
    'ethicsPolicy::ethical_issues_report': 'ethical_issues_report',
    'ethicsPolicy::ethical_issues_description': 'ethical_issues_description',
    'funder': ['project', project_mapping],
    'endDate': 'available_until',
}


host_mapping = {
    'name': 'title',
    'url': 'url',
    'description': 'description',
}


licence_mapping = {
    '@id': 'license_ref',
    'name': 'license_name',
    'startDate': 'start_date'
}


distribution_mapping = {
    '@id': 'title',
    'description': 'description',
    'contentSize': 'byte_size',
    'encodingFormat': ['format', None],
    'data_access::descrition': 'data_access',
    'contentLocation': ['host', host_mapping],
    'license': ['license', licence_mapping],
    'endDate': 'available_until',
}


dataset_mapping = {
    'identifier': 'dataset_id::identifier',
    'name': 'title',
    'description': 'description',
    'contentType': 'type',
    'keywords': 'keyword',
    'distribution': ['distribution', distribution_mapping],
    '_': {'personal_data': 'unknown'},
    '__': {'sensitive_data': 'unknown'}
}

mappings = (role_value_mapping, contributor_mapping, contact_mapping,
           cost_mapping, funder_mapping, project_mapping,
           dmp_header_to_dataset_mapping, host_mapping, licence_mapping,
           distribution_mapping, dataset_mapping)

def test_rocrate_dmp(dmp_header):
    if not 'contact' in dmp_header:
        print('argh')
        if 'contributor' in dmp_header:
            if not isinstance(dmp_header['contributor'], list):
                dmp_header['contributor'] = [copy.deepcopy(dmp_header['contributor'])]
            for contributor in dmp_header['contributor']:
                if not 'role' in contributor:
                    contributor['role'] = ['']
            dmp_header['contact'] = copy.deepcopy(dmp_header['contributor'][0])
            dmp_header['contact']['contact_id'] = dmp_header['contact'].pop('contributor_id')
    if not 'ethical_issues_exist' in dmp_header:
        dmp_header['ethical_issues_exist'] = 'unknown'
    if not 'language' in dmp_header:
        dmp_header['language'] = 'eng'
    for dataset in dmp_header['dataset']:
        for distribution in dataset['distribution']:
            if not 'data_access' in distribution:
                distribution['data_access'] = 'closed'
    


def rocrates_to_madmp(path, path_schema, mappings, dmp_identifier):
    manifest_dirs = [ name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name)) and 'manifest.jsonld' in os.listdir(os.path.join(path, name))]
    manifest_dirs.sort()
    if 'manifest.jsonld' in os.listdir(path):
        manifest_dirs.insert(0, '')
    
    dmp_id_type = get_identifer_type_for_dmp(dmp_identifier)
    dmp_header = {'title': 'DMP created from rocrates',
                 'description': 'a RDA-DMP-Common-Standard maDMP created from rocrate manifests',
                 'dmp_id': {
                     'identifier': dmp_identifier,
                     'type': dmp_id_type
                 }}
    
    dmp_from_rocrate = {'dmp': {}}
    datasets = []
    for manifest_dir in manifest_dirs:
        manifest = read_json_local(os.path.join(path, manifest_dir, 'manifest.jsonld'))
        dmp_header = {**dmp_header, **parse_mapping(manifest, dmp_header_to_dataset_mapping)}
        datasets.append(parse_mapping(manifest, dataset_mapping))
    dmp_header['dataset'] = datasets
    # add some defaults for missing keys
    test_rocrate_dmp(dmp_header)
    dmp_from_rocrate['dmp'] = dmp_header
    #print(json.dumps(dmp_from_rocrate, indent=4))
    
    
    # check schema
    schema = read_json_url(path_schema)
    valid = check_valid_dmp(dmp_from_rocrate, schema)
    
    write_json_local(os.path.join(path, 'dmp_from_rocrates.json'), dmp_from_rocrate)


#path = 'examples/ex9-dmp-long/'
#path_schema = 'https://raw.githubusercontent.com/RDA-DMP-Common/RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/1.0/maDMP-schema-1.0.json'
#dmp_identifier = "https://doi.org/10.0000/00.0.1234"
#rocrates_to_madmp(path, path_schema, mappings, dmp_identifier)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-path', '--path', type=str, required=True, help='root path to search for rocrates')   
    parser.add_argument('-path_schema', '--path_schema',
                        type=str,
                        default='https://raw.githubusercontent.com/RDA-DMP-Common/RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/1.0/maDMP-schema-1.0.json',
                        help='a url to RDA-DMP-Common schema')   
    parser.add_argument('-dmp_identifier', '--dmp_identifier',
                        type=str,
                        default='',
                        help='a unique identifier for your dmp')   
    args = parser.parse_args()

    rocrates_to_madmp(args.path, args.path_schema, mappings, args.dmp_identifier)