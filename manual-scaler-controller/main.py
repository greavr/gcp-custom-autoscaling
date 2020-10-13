from googleapiclient import discovery
import google.cloud.logging
from oauth2client.client import GoogleCredentials
from google.cloud import monitoring_v3
import os
import requests
import json
from datetime import datetime
import time
import math
import logging
import random
from re import search

# Build Credentials
credentials = GoogleCredentials.get_application_default()
LoggingClient = google.cloud.logging.Client()

# Env Variables
project = str(os.environ['GCP_PROJECT'])
region = str(os.environ['mig_region'])
instance_group_manager = str(os.environ['mig_name'])

# Get all Instances in Managed Instance Group
def GetInstanceList():
    # Use global variables
    global credentials, project, region, instance_group_manager
    # Query for list of instances
    service = discovery.build('compute', 'v1', credentials=credentials)
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

# Get all Cloud Schedule jobs with this MIG name
def GetCurrentSchedule():
    global credentials, project, region, instance_group_manager
    service =  discovery.build('cloudscheduler', 'v1', credentials=credentials)

    # Build Parent Path
    parent = f'projects/{project}/locations/{region}'

    # Build the request and execute
    request = service.projects().locations().jobs().list(parent=parent)
    ResultList = []
    while True:
        response = request.execute()
        # Itterate over found jobs
        for job in response.get('jobs', []):
            # Filter the results for only those matching this MIG
            JobName = str(job["name"]).lower()
            if search(instance_group_manager.lower(), JobName):
                aJob = {"name" : job["name"], "schedule" : job["schedule"], "state": job["state"]}
                ResultList.append(aJob)

        request = service.projects().locations().jobs().list_next(previous_request=request, previous_response=response)
        if request is None:
            break

    return ResultList

# OutPut Formatter
def OutPutFormat(Instances,TaskSchedule):
    pass

# Disable Schedule
def DisableSchedule(ScheduleName):
    pass

# Enable Schedule
def EnableSchedule(ScheduleName):
    pass



#Main Function handler
def main(request):
    global LoggingClient

    # App Variables
    InstanceList = []
    CurrentSchedule = []

    # Setup the logger
    LoggingClient.get_default_handler()
    LoggingClient.setup_logging()
    
    
    # Main Loop
    ## Get list of instances in MIG
    InstanceList = GetInstanceList()

    ## Get Current schedule for the Autoscaler
    CurrentSchedule = GetCurrentSchedule()

    ReturnHtml = OutPutFormat(Instances=InstanceList,TaskSchedule=CurrentSchedule)
    print (CurrentSchedule)


if __name__ == "__main__":
    main("")