import json
import logging
import math
import os
import random
import sys
import time
from datetime import datetime

import google.cloud.logging
import requests
from google.cloud import datastore, monitoring_v3, pubsub_v1
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# Build Credentials
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)
LoggingClient = google.cloud.logging.Client()

# Env Variables
project = os.environ['GCP_PROJECT']
region = os.environ['mig_region']
instance_group_manager = os.environ['mig_name']
ScaleUpThreshold = int(os.environ['upper_session_count'])
lower_mig_size = int(os.environ['lower_mig_size'])
pubsub_topic = os.environ['pub_sub_topic']

# App Variables
InstanceList = []

# Publish Topic Notification():
def PublishPubSub(Type,Body):
    global pubsub_topic
    # Function to pass messages, two types:
    ## Add - Created New Instance, msg body includes new instance name, zone and private IP
    ## Remove - Removed Instances, msg body is a list of removed instances, with name

    # Format list for PubSub
    if type(Body) is list:
        Body = ','.join(map(str, Body)) 

    try:
        publisher = pubsub_v1.PublisherClient()
        publisher.publish(pubsub_topic,data = Body.encode('utf-8'),Type="True")
        logging.info(f"Published PubSub MSG {Type}, {Body}. To the following Topic: {pubsub_topic}")
    except:
        e = sys.exc_info()[0]
        logging.error(f"Failed to publish PubSub MSG {Type}, {Body}. To the following Topic: {pubsub_topic}. Error Message {e}")

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
    PubSubMsg = []
    for aInstance in InstanceList:
        serverString = f"zones/{InstanceList[aInstance]}/instances/{aInstance}"
        FormatedInstances.append(serverString)
        PubSubMsg.append({ "Name" : aInstance})


    RequestBody = {}
    RequestBody["instances"] = FormatedInstances

    #Build and send the request
    try:
        request = service.regionInstanceGroupManagers().deleteInstances(project=project, region=region, instanceGroupManager=instance_group_manager, body=RequestBody)
        response = request.execute()
        logging.info(response)
        # Update PubSub
        PublishPubSub("RemoveServers",PubSubMsg)
    except:
        e = sys.exc_info()[0]
        logging.error(f"Unable to remove instances from MIG. Error Message: {e}")

#Function Add Instance to MIG
def AddInstance(NewSize):
    global service, credentials, project, instance_group_manager, region

    try:
    # First try to increase MIG size, then report the list of servers
        request = service.regionInstanceGroupManagers().resize(project=project, region=region, instanceGroupManager=instance_group_manager, size=NewSize)
        response = request.execute()
        logging.info(f"Increased the Managed Instance Group {instance_group_manager} to size of {NewSize}")

        # Get List Of instances
        NewList = GetInstanceList()
        #Format list for pubsub
        NewInstanceList = []
        for aInstance in NewList:
            instanceIp = GetInstanceIP(zone=aInstance["zone"],instance=aInstance["name"])
            aServer = { "Name" : aInstance["name"], "IP" : instanceIp}
            NewInstanceList.append(aServer)
        
        #Send PubSub Message
        PublishPubSub("NewServerList",NewInstanceList)
    except:
        e = sys.exc_info()[0]
        logging.error(f"Failed to increase the Managed Instance Group {instance_group_manager} to size of {NewSize}. Error Message {e}")
        
# Handle Autoscaling
def Autoscale():
    global InstanceList, service, credentials, project, region, instance_group_manager, ScaleUpThreshold, lower_mig_size
    # Function to autoscale the Managed instance group
    TotalSessionCount = 0
    AverageSessionCount = 0
    ScaleDownCount = 0
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
    try:
        # Used to catch 0 sessions on all nodes
        AverageSessionCount = round(TotalSessionCount/ServerCountAfterScaleDown)
    except:
        AverageSessionCount = 0
    logging.info("Currently have %s Sessions over %s hosts, with an average of %s on None-zero session servers",str(TotalSessionCount),str(ServerCountAfterScaleDown),str(AverageSessionCount))

    # Autoscale up logic
    if AverageSessionCount >= ScaleUpThreshold:
        # First check if there is an currently empty server which can be used
        if ScaleDownCount > 0:
            ScaleDownCount -= 1
            logging.info("Not resizing due to instance with 0 sessions found")
            ScaleDownInstanceList.popitem()
        else:
            # If not add a Server
            NewSize = len(InstanceList)+1
            AddInstance(NewSize)
    
    # Autoscale down logic
    ## First Ensure that Scale down will not break the lower bound
    TargetServerCount = len(ScaleDownInstanceList) - lower_mig_size
    NumToRemove = len(ScaleDownInstanceList) - TargetServerCount
    logging.info(f"Number of servers to be spared from remove list: {NumToRemove}. Total servers to be removed: {str(TargetServerCount)}")
    if NumToRemove >= 1:
        #Loop Through Popping
        count = 0
        while (count < NumToRemove):
            count += 1
            ScaleDownInstanceList.popitem()
            ScaleDownCount -= 1

        # Itterate through instances and remove them
        logging.info(f"Scaling down {ScaleDownInstanceList} due to 0 sessions")
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
    global InstanceList, LoggingClient, instance_group_manager, lower_mig_size

    # Setup the logger
    LoggingClient.get_default_handler()
    LoggingClient.setup_logging()
      
    # Main Loop
    InstanceList = GetInstanceList()
    ServerCount = len(InstanceList)
    logging.info(f"Autoscaling the Instance Group: {instance_group_manager}, current size is: {ServerCount}, and Minimum size set is: {lower_mig_size}")

    # Itterate over instances to get session count
    ReviewInstances()

    # Save Session Count to Stackdriver
    LogMetrics()

    # If the list is the same size than the Lower Mig size then escape now:
    if ServerCount > lower_mig_size:
        # Autoscale
        Autoscale()
    elif ServerCount < lower_mig_size:
        logging.info(f"Instance Group: {instance_group_manager}, current size is: {ServerCount}, and Minimum size set is: {lower_mig_size}. Resizing to minimum size")
        AddInstance(lower_mig_size)  

    # Save Values to DS
    SaveToDatastore()

    # Validate output
    return json.dumps(InstanceList)

if __name__ == "__main__":
    MainThread("")