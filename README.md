# maDMP-rocrates-maDMP
[![DOI](https://zenodo.org/badge/275586451.svg)](https://zenodo.org/badge/latestdoi/275586451)


## Task description

RO-Crate[5]
is a community effort to establish a lightweight approach to packaging research data with
their metadata. It is based on schema.org annotations in JSON-LD, and aims to make best-practice in
formal metadata description accessible and practical for use in a wider variety of situations, from an
individual researcher working with a folder of data, to large data-intensive computational research
environments.

Machine-actionable DMPs[6]
(maDMPs) are an emerging standard for exchange of DMPs between
systems involved in research data management. There are certain overlaps in the scope of maDMPs
and ro-crates. Reuse and transfer of information between the maDMPs and ro-crates can facilitate
adoption of both and reduce workload imposed on researchers to document their data.
In this task you will:
- Define a mapping between ro-crate 1.0 and maDMPs
- Develop a tool that
  - Extracts relevant information from an maDMP and creates ro-crates [1 to many]
  - Reuses information from ro-crates to generate a maDMP [many to 1]
To test your mapping and the tool, you will:
- Extract information from maDMPs to create ro-crates
  - 5 selected maDMPs from the Data Stewardship community[7]
  - 5 examples from the RDA Repository[8]
(must include ex9-dmp-long)
- Use information from ro-crates to fill in maDMPs
  - 3 example RO-crates from the official ro-crate website
  - 2 realistic examples of RO-crates created by you to test the coverage of your mapping
Don’t forget to validate the generated maDMPs against the provided JSON schema. The mapping must
be as complete as possible.

[5] https://researchobject.github.io/ro-crate/  
[6] https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard  
[7] https://zenodo.org/communities/tuw-dmps-ds-2020/  
[8] https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard/tree/master/examples/JSON  

## Prerequisites
developed using python 3.7.5
```bash
# create environment
python -m venv datasteward_venv

# activate venv
source datasteward_venv/bin/activate

# install requirements
pip install -r requirements.txt
```

## Running scripts and examples
**core scripts**  
To convert a dmp to multiple rocrates:  
```bash
python src/madmp_to_rocrates.py -path <path to madmp file> [-path_schema <url to RDA-DMP-Common-Standard schema>]
```
To convert rocrates to maDMP:
```bash
python src/rocrates_to_madmp.py -path <root path to search for rocrates> [-path_schema <url to RDA-DMP-Common-Standard schema>] [-dmp_identifier <madmp unique identifier>]
```
To compare the 2 maDMP's
```bash
python src/compare_dictionaries.py -path_d1 <path to dict 1> -path_d2 <path to dict 2> [-path_report <path where comparison report is saved>]
```

**examples**  
A jupyter notebook (notebooks/run_examples.ipynb) runs several examples of converting maDMP to rcrates and back as well as rocrate to DMP

## Implementation
The initial and working implementation used the ro-crate 0.1.0 definitions. Bringing this in line with ro-crate 1.0 is under development in in the development branch. The following references the ro-crate 0.1.0 version.

###Mappings:
The following uses the syntax:  
- ```<madmp key(s)>: <rocrate key(s)> ```
- key1::key2 for nested keys in both read and write columns
- '-': dict to insert values into rocrate
- ```<madmp key(s)>: [<rocrate key(s)>, <mappingg for nessted dict>]```

```python
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
```
### comments
The main problems were:
- ro-crate temporalCoverage as this requires 'start/stop' for the dataset which the dmp doesnt
- the dmp data_access value doesnt map to an instance or property of ro-crate. The proposed solution was to create a sub dict with the dataset id as @id and add type @ActiveActionStatus plus the dmp value. The ActiveActionStatus is not a good match.
- ro-crate requires a datePublished for the dataset, which is absent in the dmp but the dmp value modified was used but modified actually refers to teh dmp itself and not the datasets within.
- the dmp proerties ethical_issues_exist, ethical_issues_report and ethical_issues_description were put in a sub dict with type ethicsPolicy, which was not a terrible fit but refers to an actual policy document and the dmp properties were simple mpoved there 1:1
- similarly i could not find a ro-crate class or instance that covered the dmp dataset properies peronal_data and sensitive_data. These were omitted.
- The dmp identifer is also absent from the produced ro-crate as the top level identifier is that of the dataset. The solution for ro-crate to dmp was to have a user input for he dmp identifier, which also makes sense if the task is to convert ro-crates to a dmp where a dmp doesnt exist
- dmp->dataset->distribution->host geo_location, pid_system and support versioning are absent
- dmp dataset properties data_quality_assurance, metadata, preservation_statement, security_and_privacy, technical_resource are absent
- I tried to do it by parsing dicts and lists through the nested structures. This basically will never work and in particular for the flat structure of ro-crate 1.0

## Comments
Continuing this project would require a complete restructure and essentially create a ro-crate line by line using the values from the dmp, similarly to this <https://github.com/ResearchObject/ro-crate-py>. Similarly, for the ro-crate to dmp. 