from googleapiclient import discovery
import google.cloud.logging
from oauth2client.client import GoogleCredentials
from google.cloud import monitoring_v3
from google.cloud import datastore
import os
from pprint import pprint
import requests
import json
from datetime import datetime
import time
import math
import logging
import random

# Build Credentials
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)
LoggingClient = google.cloud.logging.Client()

# Env Variables
project = os.environ['GCP_PROJECT']
region = os.environ['mig_region']
instance_group_manager = os.environ['mig_name']
ScaleUpThreshold = int(os.environ['upper_session_count'])

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
        ResultList.append(aServer)

    if not ResultList:
        logging.error("Unable to find any hosts in %s MIG, in the %s region",str(instance_group_manager),str(region))
    else:
        logging.info("Found %s instances in the %s MIG",str(len(ResultList)),str(instance_group_manager))
    #Return value
    return ResultList

# Get instance info
def GetInstanceIP(zone,instance):
    # Use global variables
    global service, credentials, project, region, instance_group_manager
    try:
        request = service.instances().get(project=project, zone=zone, instance=instance)
        response = request.execute()
        # Parse out key information
        valueToFind = "networkIP" # InternalIP
        external_ip = response["networkInterfaces"][0]["networkIP"]
    except:
        logging.error("Unable to find IP for %s in the %s zone",str(instance),str(zone))
        external_ip = "0.0.0.0"

    return external_ip

# Get current Session count
def GetSessionCount(InstanceIP):
    # Make a request to curl a instance to get session count
    url = "http://" + InstanceIP + ":8080/"
    try:
        response = requests.get(url, timeout=2)
        return response.json()['SessionCount']
    except:
        logging.error("Unable to get session count from http://" + InstanceIP + ":8080/")
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

# Function to save metrics to stackdriver
def LogMetrics():
    global service, credentials, project, InstanceList, instance_group_manager
    # Itterate through metrics and save to GCP Stackdriver

    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{project}"
    # Itterate Through instances
    for aInstance in InstanceList:
        # Only add values if session count is not -1
        if (aInstance['session_count'] != -1):
            series = monitoring_v3.types.TimeSeries()
            series.metric.type = 'custom.googleapis.com/sessions/session_count'
            series.resource.type = 'gce_instance'
            series.resource.labels['instance_id'] = aInstance['name']
            series.resource.labels['zone'] = aInstance['zone']
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10 ** 9)
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            point = monitoring_v3.Point({"interval": interval, "value": {"double_value": aInstance['session_count']}})
            series.points = [point]
            client.create_time_series(request={"name": project_name, "time_series": [series]})

#Function To Remove Instance from MIG
def RemoveServers(InstanceList):
    global service, credentials, project, instance_group_manager, region

    #Build the request body
    ## Build instance url zones/{ZONE}/instances/{INSTANCE NAME}
    FormatedInstances = []
    for aInstance in InstanceList:
        serverString = f"zones/{InstanceList[aInstance]}/instances/{aInstance}"
        FormatedInstances.append(serverString)


    RequestBody = {}
    RequestBody["instances"] = FormatedInstances

    #Build and send the request
    try:
        request = service.regionInstanceGroupManagers().deleteInstances(project=project, region=region, instanceGroupManager=instance_group_manager, body=RequestBody)
        response = request.execute()
    except:
        logging.error("Unable to remove instances from MIG")

#Function Add Instance to MIG
def AddInstance(NewSize):
    global service, credentials, project, instance_group_manager, region
    request = service.regionInstanceGroupManagers().resize(project=project, region=region, instanceGroupManager=instance_group_manager, size=NewSize)
    response = request.execute()

# Handle Autoscaling
def Autoscale():
    global InstanceList, service, credentials, project, region, instance_group_manager, ScaleUpThreshold, ScaleDownThreshold
    # Function to autoscale the Managed instance group
    TotalSessionCount = 0
    AverageSessionCount = 0
    ScaleDownCount = 0
    ScaleUpValue = 0
    ScaleDownInstanceList = {}
    
    # First get current status
    for aInstance in InstanceList:
        # Get count of total instances
        TotalSessionCount += aInstance['session_count']

        # Check to see if instance is empty
        if (aInstance['session_count'] == 0):
            ScaleDownInstanceList[aInstance['name']] = aInstance['zone']
            ScaleDownCount += 1

    # Now check to see how many servers need to be added
    ServerCountAfterScaleDown = len(InstanceList)-ScaleDownCount
    AverageSessionCount = round(TotalSessionCount/ServerCountAfterScaleDown)
    logging.info("Currently have %s Sessions over %s hosts, with an average of %s on None-zero session servers",str(TotalSessionCount),str(ServerCountAfterScaleDown),str(AverageSessionCount))

    # Autoscale up logic
    if AverageSessionCount >= ScaleUpThreshold:
        # First check if there is an currently empty server which can be used
        if ScaleDownCount > 0:
            ScaleDownCount -= 1
            logging.info("Not resizing due to instance with 0 sessions found")
            ScaleDownInstanceList.pop(0)
        else:
            # If not add a Server
            NewSize = len(InstanceList)+1
            logging.info("Increasing %s MIG size to %s", str(instance_group_manager), str(NewSize))
            AddInstance(NewSize)
    
    # Autoscale down logic
    if ScaleDownCount > 0:
        # Itterate through instances and remove them
        logging.info("Scaling down %s due to 0 sessions", str(ScaleDownInstanceList))
        RemoveServers(ScaleDownInstanceList)

# Save Values to Datastore
def SaveToDatastore():
    global instance_group_manager, InstanceList,project
    # Save values to Datastore for the recommender Service
    datastore_client = datastore.Client(project=project)

    # The kind for the new entity
    kind = 'Session_levels'

    # The name/ID for the new entity
    name = instance_group_manager

    # The Cloud Datastore key for the new entity
    task_key = datastore_client.key(kind, name)

    # Prepares the new entity
    task = datastore.Entity(key=task_key)
    for aInstance in InstanceList:
        task[aInstance["name"]] = aInstance["session_count"]

    # Saves the entity
    datastore_client.put(task)


## Main Loop
def MainThread(request):
    global InstanceList, LoggingClient

    # Setup the logger
    LoggingClient.get_default_handler()
    LoggingClient.setup_logging()
    
    
    # Main Loop
    InstanceList = GetInstanceList()

    # Itterate over instances to get session count
    ReviewInstances()

    # Save Session Count to Stackdriver
    LogMetrics()

    # Autoscale
    Autoscale()

    # Save Values to DS
    SaveToDatastore()

    # Validate output
    return json.dumps(InstanceList)

if __name__ == "__main__":
    MainThread("")
