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
            #d_out[v] = value
            d_out = nested_set(d_out, v, value)
    return d_out

def parse_list(lst, d, mapping):
    lst_out = []
    for item in lst:
        if isinstance(item, dict):
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

rocrate_header = {
        "@context": ["http://schema.org", "https://w3id.org/bundle/context"],
        "@type": ["ro:ResearchObject", "Dataset"],
        "@id": ".",
    }

role_value_mapping = {
    'contributor_id::identifier': '@id',
    '_': {'@type': 'Role'},
    '__': {'name': 'item'}
}

contributor_mapping = {
    'contributor_id::identifier': '@id',
    '_': {'@type': 'Person'},
    #'contributor_id::type': 'type',
    'mbox': 'email',
    'name': 'name',
    'role': ['roleName', role_value_mapping],
}

contact_mapping = {
    'contact_id::identifier': '@id',
    #'contact_id::type': 'type',
    'mbox': 'email',
    'name': 'name'
}

cost_mapping = {
    'title': '@id',
    '_': {'@type': 'Cost'},
    'currency_code': 'costCurrency',
    'description': 'description',
    'value': 'value',
}

funder_mapping = {  # list
    'grant_id::identifier': '@id',
    '_': {'@type': 'Grant'},
    'funder_id::identifier': 'funder::@id',
    '__': {'funder::@type': 'Organisation'},
    'funding_status': 'description',
}

project_mapping = {
    "project_id": '@id',  # add ('@type': "Project") after @id 
    '_': '@type: Project',
    "title": "name",
    #"project_id_type": "type",
    "start": "startDate",  # on top level temporalCoverage = "temporalCoverage_i/temporalCoverage_f"
    "end": "endDate",
    "description": "description",
    "funding": ['funder', funder_mapping],  # list to list
}

dmp_header_to_dataset_mapping = {
    'language': 'language',
    'created': 'dateCreated',
    'modified': 'datePublished',
    'contact': ['contactPoint', contact_mapping],
    'contributor': ['creator', contributor_mapping],
    'cost': ['cost', cost_mapping],
    '_': {'ethicsPolicy::@type': 'CreativeWork'},
    'ethical_issues_exist': 'ethicsPolicy::ethical_issues_exist',
    'ethical_issues_report': 'ethicsPolicy::ethical_issues_report',
    'ethical_issues_description': 'ethicsPolicy::ethical_issues_description',
    'project': ['funder', project_mapping],
    'available_until': 'endDate',
}


host_mapping = {
    'title': 'name',
    'host::url': 'url',
    '_': {'@type': 'RepositoryCollection'},
    'description': 'description',
}


licence_mapping = {
    'license_ref': '@id',
    '_': {"@type": "CreativeWork"},
    'license_name': 'name',
    'start_date': 'startDate'
}


distribution_mapping = {
    'title': '@id',
    'description': 'description',
    'byte_size': 'contentSize',
    'format': ['encodingFormat', None],
    '_': {'data_access::@type': 'ActiveActionStatus'},
    'data_access': 'data_access::descrition',
    'host': ['contentLocation', host_mapping],
    'license': ['license', licence_mapping],
    'available_until': 'endDate',
}


dataset_mapping = {
    '_': {'@id': '.'},
    'dataset_id::identifier': 'identifier',
    'title': 'name',
    'description': 'description',
    'type': 'contentType',
    'keyword': ['keywords', 'list_to_str'],
    'distribution': ['distribution', distribution_mapping],
}

mappings = (rocrate_header, role_value_mapping, contributor_mapping, contact_mapping,
           cost_mapping, funder_mapping, project_mapping,
           dmp_header_to_dataset_mapping, host_mapping, licence_mapping,
           distribution_mapping, dataset_mapping)


def madmp_to_rocrate(path,
                     path_schema,
                     mappings):
    
    rocrate_header, role_value_mapping, contributor_mapping, contact_mapping, \
           cost_mapping, funder_mapping, project_mapping, \
           dmp_header_to_dataset_mapping, host_mapping, licence_mapping, \
           distribution_mapping, dataset_mapping = mappings
    
    # read dmp
    dmp = read_json_local(path)
    
    # check schema
    schema = read_json_url(path_schema)
    valid = check_valid_dmp(dmp, schema)
    if not valid:
        sys.exit(1)
    
    # get dmp content
    dmp_0 = dmp['dmp']
    # get dmp top level info
    rocrate_dmp_part = parse_mapping(dmp_0, dmp_header_to_dataset_mapping)
    # vreate rocrate for each dataset
    rocrates = []
    n_datasets = len(dmp_0['dataset'])
    for i, dataset in enumerate(dmp_0['dataset']):
        print('processing dataset {} of {} datasets'.format(i+1, n_datasets))
        rocrate_dataset = {}
        rocrate_dataset = parse_mapping(dataset, dataset_mapping)

        rocrate_header.update(rocrate_dataset)
        rocrate_header.update(rocrate_dmp_part)
        rocrates.append(copy.deepcopy(rocrate_header))

        #print(json.dumps(rocrate_header, indent=4))
        
    # write rocrates to disk
    write_rocrates(path, rocrates)




#path = 'exercise2/examples/ex9-dmp-long/ex9-dmp-long-mod.json'
#path_schema = 'https://raw.githubusercontent.com/RDA-DMP-Common/RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/1.0/maDMP-schema-1.0.json'
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-path', '--path', type=str, required=True, help='path to maDMP file. Also where manifest will be written')   
    parser.add_argument('-path_schema', '--path_schema',
                        type=str,
                        default='https://raw.githubusercontent.com/RDA-DMP-Common/RDA-DMP-Common-Standard/master/examples/JSON/JSON-schema/1.0/maDMP-schema-1.0.json',
                        help='a url to RDA-DMP-Common schema')   
    args = parser.parse_args()

    madmp_to_rocrate(args.path, args.path_schema, mappings)