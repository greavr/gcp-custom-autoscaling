from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google.cloud import monitoring_v3
import os
from pprint import pprint
import requests
import json
from datetime import datetime
import time
import math

# Build Credentials
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)

# Env Variables
project = os.environ['GCP_PROJECT']
region = os.environ['mig_region']
instance_group_manager = os.environ['mig_name']
ScaleUpThreshold = int(os.environ['upper_session_count'])
ScaleDownThreshold = int(os.environ['lower_session_count'])

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

# Function to save metrics to stackdriver
def LogMetrics():
    global service, credentials, project, InstanceList
    # Itterate through metrics and save to GCP Stackdriver

    client = monitoring_v3.MetricServiceClient()
    project_name = client.project_path(project)
    # Itterate Through instances
    for aInstance in InstanceList:
        # Only add values if session count is not -1
        if (aInstance['session_count'] != -1):
            series = monitoring_v3.types.TimeSeries()
            series.metric.type = 'custom.googleapis.com/sessions/session_count'
            series.resource.type = 'gce_instance'
            series.resource.labels['instance_id'] = aInstance['name']
            series.resource.labels['zone'] = aInstance['zone']
            point = series.points.add()
            point.value.double_value = aInstance['session_count']
            now = time.time()
            point.interval.end_time.seconds = int(now)
            point.interval.end_time.nanos = int(
                (now - point.interval.end_time.seconds) * 10**9)
            client.create_time_series(project_name, [series])

# Handle Autoscaling
def Autoscale():
    global InstanceList, service, credentials, project, region, instance_group_manager, ScaleUpThreshold, ScaleDownThreshold
    # Function to autoscale the Managed instance group
    TotalSessionCount = 0
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
    
    # Check ratio of overall server count * ScaleUpThreshold to see if we need more servers
    print("Currently have %s Sessions over %s hosts (after scaledown)" % (TotalSessionCount,len(InstanceList)-ScaleDownCount))
    print("Going to scale down %s servers" %(ScaleDownCount))
    safeSessionTotal = (len(InstanceList)-ScaleDownCount) * ScaleUpThreshold
    if (safeSessionTotal >= TotalSessionCount):
        ScaleUpValue = math.ceil((TotalSessionCount-safeSessionTotal)/ScaleUpThreshold)
        print("Scaling up by %s sessions" % (ScaleUpValue))



## Main Loop
def MainThread(request):
    global InstanceList
    
    # Main Loop
    InstanceList = GetInstanceList()
    # Itterate over instances to get session count
    ReviewInstances()

    # Save Session Count to Stackdriver
    LogMetrics()

    # Autoscale
    Autoscale()

    # Validate output
    pprint(InstanceList)
    return json.dumps(InstanceList)
    

if __name__ == "__main__":
    MainThread("Blah")
