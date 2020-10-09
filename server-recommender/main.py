from googleapiclient import discovery
import google.cloud.logging
from oauth2client.client import GoogleCredentials
from google.cloud import monitoring_v3
from google.cloud import datastore
import os
import requests
import json
from datetime import datetime
import time
import math
import logging
import random

# Build Credentials
credentials = GoogleCredentials.get_application_default()
LoggingClient = google.cloud.logging.Client()

# Env Variables
project = os.environ['GCP_PROJECT']
instance_group_manager = os.environ['mig_name']
OptimalSessionCount = int(os.environ['upper_session_count']) - 1

# App Variables
InstanceList = {}

# Get values from datastore
def GetValues():
    global instance_group_manager, InstanceList, project
    # Load values from Datastore
    datastore_client = datastore.Client(project=project)

    # The kind for the new entity
    kind = 'Session_levels'

    # The name/ID for the new entity
    name = instance_group_manager

    # Find value
    key = datastore_client.key(kind, name)
    results = datastore_client.get(key)

    # Setup Results
    for aValue in results.items():
        InstanceList[str(aValue[0])] = int(aValue[1])

    InstanceList = sorted(InstanceList.items(), key=lambda x: x[1], reverse=True)

    logging.info(InstanceList)

# Save updated values to Datastore
def SaveToDatastore():
    global instance_group_manager, InstanceList, project
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
        task[aInstance[0]] = aInstance[1]

    # Saves the entity
    datastore_client.put(task)

## Main Loop
def MainThread(request):

    # Setup the logger
    LoggingClient.get_default_handler()
    LoggingClient.setup_logging()

    # Function loads session count from Datastore and recommends instances closest too but not over OptimalSessionCount
    GetValues()

    # Recommend a server based on first server which is closest to OptimalSessionCount
    RecommendInstance = ""
    x = 0
    ## Itterate over instances in list
    for aInstance in InstanceList:
        ## First check if we found a server with OptimalSessionCount
        if aInstance[1] <= OptimalSessionCount:
            RecommendInstance = aInstance[0]
            InstanceList[x] = { InstanceList[x][0] : InstanceList[x][1] + 1 }
            break
        x += 1
    
    # If not found a server with capacity pick the server with the lowest Session Count
    if RecommendInstance == "":
        RecommendInstance = InstanceList[-1][0]
        InstanceList[-1] = { InstanceList[-1][0] : InstanceList[-1][1] + 1 }

    # Logging info
    logging.info(f"Recommended instance {RecommendInstance} in {instance_group_manager}")

    # Write New Data to Datastore
    SaveToDatastore()

    return(jsonify(RecommendInstance))



if __name__ == "__main__":
    MainThread("")