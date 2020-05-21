'''
Created on Mar 19, 2019

@author: Steven.Colon
'''
import requests
import json
import math
import helper_functions


with open('config.json', 'r') as file:
    config = json.load(file)

export_org_api_key= config['EXPORTORG']['API_KEY']
export_org_registry_basepath = config['EXPORTORG']['REGISTRY_API_BASEPATH']
export_org_name = config['EXPORTORG']['ORG']
export_org_limit = config['EXPORTORG']['LIMIT']

import_org_api_key= config['IMPORTORG']['API_KEY']
import_org_registry_basepath = config['IMPORTORG']['REGISTRY_API_BASEPATH']
import_org_name = config['IMPORTORG']['ORG']
private_visibility = config['IMPORTORG']['DEFAULT_PRIVATE_VISIBILITY']

#check for boolean type in config
if not type(private_visibility) is bool:
    raise TypeError("DEFAULT_PRIVATE_VISIBILITY needs to be a boolean value")

def main():
    #URL to pull/push API Specs
    export_org_registry_api = export_org_registry_basepath +"apis/"
    import_org_registry_api = import_org_registry_basepath + "apis/"
    
    #Get number of API Specs pages
    org_specs_call = requests.get(export_org_registry_api + export_org_name, headers= {'Authorization': export_org_api_key}, params= {'limit': 1, 'page': 0})
    org_apis_json = org_specs_call.json()

    if len(org_apis_json['apis']) == 0:
        raise RuntimeError("No APIs Found to export")

    org_apis_num_pages = math.floor(org_apis_json["totalCount"] / export_org_limit)

    #Pull specs in the outgoing org
    org_apis_page = 0
    while org_apis_page <= org_apis_num_pages:
        org_specs_call = requests.get(export_org_registry_api + export_org_name, headers= {'Authorization': export_org_api_key}, params= {'limit': export_org_limit, 'page': org_apis_page})
        org_apis_json = org_specs_call.json()
    
        print("Migrating Page " + str(org_apis_page + 1) + " of " + str(org_apis_num_pages + 1) + " with " + str(len(org_apis_json['apis'])) + " OAS Specs (Total: " + str(org_apis_json["totalCount"]) + ")"
            + " from " + export_org_registry_api + export_org_name + " to " + import_org_registry_api + import_org_name)
    
        parse_org(org_apis_json, export_org_registry_api, import_org_registry_api)
        org_apis_page += 1
    
    
    export_org_domains_url = export_org_registry_basepath + "domains/"
    import_org_domains_url = import_org_registry_basepath + "domains/"

    #Get number of Domains pages
    export_org_domains_call = requests.get(export_org_domains_url + export_org_name, headers= {'Authorization': export_org_api_key}, params= {'limit': 1, 'page': 0})
    export_org_domains_json = export_org_domains_call.json()

    if len(export_org_domains_json['apis']) == 0:
        print("No Domains Found to export")

    export_org_domains_num_pages = math.floor(export_org_domains_json["totalCount"] / export_org_limit)

    #Pull domains in the outgoing org
    export_org_domains_page = 0
    while export_org_domains_page <= export_org_domains_num_pages:
        export_org_domains_call = requests.get(export_org_domains_url + export_org_name, headers= {'Authorization': export_org_api_key}, params= {'limit': export_org_limit, 'page': export_org_domains_page})
        export_org_domains_json = export_org_domains_call.json()
    
        print("Migrating Page " + str(export_org_domains_page + 1) + " of " + str(export_org_domains_num_pages + 1) + " with " + str(len(export_org_domains_json['apis'])) + " Domains (Total: " + str(export_org_domains_json["totalCount"]) + ")"
            + " from " + export_org_registry_api + export_org_name + " to " + import_org_registry_api + import_org_name)
    
        parse_org(export_org_domains_json, export_org_domains_url, import_org_domains_url)
        export_org_domains_page += 1


def parse_org(org_json, export_url, import_url):
    for metadata in org_json["apis"]:
        #Remove Default Version number from API Url so that we can pull all versions
        url = metadata["properties"][0]["url"] 
        last_slash = url.rindex('/', 0)
        formatted_url = url[0: last_slash]
        formatted_url = helper_functions.verify_http_type(formatted_url, export_url)
        
        #Pull name of spec in SwaggerHub (different from the real name of the spec)
        sh_name = formatted_url[formatted_url.rindex('/', 0) + 1 : len(formatted_url)]
        print("Name - " + sh_name)
        print("Pulling versions from " + formatted_url)
    
        #Pull json that shows each version of the spec 
        versions_call= requests.get(formatted_url, headers={'Authorization': export_org_api_key})
        versions_json = versions_call.json()
    
        print("Found " + str(versions_json["totalCount"]) + " versions ...")
        
        export_versions(versions_json, sh_name, export_url, import_url)

def export_versions(versions_json, sh_name, export_url, import_url):
    #Pull API Version URLs
    for version in versions_json['apis']:
        api_version_url = helper_functions.verify_http_type(version["properties"][0]["url"], export_url)
        print(api_version_url)
        version_number = version["properties"][1]["value"]
        #Get spec of single API Version
        api_version_spec_call = requests.get(api_version_url, headers = {'Authorization': export_org_api_key})
        
        #push spec to OnPrem 
        import_org_post_url = import_url + import_org_name + "/" + sh_name + '?isPrivate=' + str(private_visibility) + '&version=' + version_number
        
        api_version_spec_json = api_version_spec_call.json()
        
        print("Posting Spec to - " + import_org_post_url)
        
        import_version(import_org_post_url, api_version_spec_json)
            
    print("\n")
        
        
def import_version(import_org_post_url, api_version_spec_json):
    onprem_post_call = requests.post(import_org_post_url, headers={'Authorization': import_org_api_key}, json=api_version_spec_json)
        
    if(onprem_post_call.status_code != 201 and onprem_post_call.status_code != 200):
        raise RuntimeError("Invalid OnPrem API Response - " + onprem_post_call.text)
        
main()

    


        

