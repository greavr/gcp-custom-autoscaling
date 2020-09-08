from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import os
from pprint import pprint
import requests
import json
from datetime import datetime

# Build Credentials
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)

# Env Variables
project = os.environ['GCP_PROJECT']
region = os.environ['mig_region']
instance_group_manager = os.environ['mig_name']

# App Variables
InstanceList = []

# Get all Instances in Managed Instance Group
def GetInstanceList():
    # Use global variables
    global service, credentials, project, region, instance_group_manager
    # Query for list of instances
    request = service.regionInstanceGroupManagers().listManagedInstances(project=project, region=region, instanceGroupManager=instance_group_manager)
    response = request.execute()
    # Create a dictonary response
    ResultList = []
    for instance in response['managedInstances']:
        # Parse the URL, get the path then break down to key values
        url = instance['instance']
        thisZone = url.split("/")[8]
        thisHost = url.split("/")[10]
        aServer = { 'name' : thisHost, "zone" : thisZone }
        print ("Found: " + thisHost)
        ResultList.append(aServer)

    #Return value
    return ResultList

# Get instance info
def GetInstanceIP(zone,instance):
    # Use global variables
    global service, credentials, project, region, instance_group_manager
    request = service.instances().get(project=project, zone=zone, instance=instance)
    response = request.execute()
    # Parse out key information
    valueToFind = "networkIP" # InternalIP
    try:
        external_ip = response["networkInterfaces"][0]["networkIP"]
    except:
        external_ip = "0.0.0.0"

    return external_ip

# Get current Session count
def GetSessionCount(InstanceIP):
    # Make a request to curl a instance to get session count
    url = "http://" + InstanceIP + ":8080/"
    try:
        response = requests.get(url)
        return response.json()['SessionCount']
    except:
        return -1

# Main Function for reviewing instances
def ReviewInstances():
    global InstanceList
    # Itterate over instances in InstanceList
    tempList = []
    for aInstance in InstanceList:
        #Get the instance IP
        instanceIp = GetInstanceIP(zone=aInstance["zone"],instance=aInstance["name"])
        aInstance.update({"ip": instanceIp})
        # Get session count
        instanceSessions = GetSessionCount(instanceIp)
        aInstance.update({"session_count": instanceSessions})
        tempList.append(aInstance)

    #Update list
    InstanceList = tempList

## Main Loop
def MainThread(request):
    global InstanceList
    
    # Main Loop
    InstanceList = GetInstanceList()
    # Itterate over instances to get session count
    ReviewInstances()

    # Validate output
    pprint(InstanceList)
    return f'InstanceList'
    

if __name__ == "__main__":
    MainThread("Blah")