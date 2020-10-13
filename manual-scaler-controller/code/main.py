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
from flask import Flask, render_template, flash, request, redirect
import base64

# Build Credentials
credentials = GoogleCredentials.get_application_default()
LoggingClient = google.cloud.logging.Client()

# Setup the logger
LoggingClient.get_default_handler()
LoggingClient.setup_logging()

# App Config
app = Flask(__name__)


# Env Variables
project = str(os.environ['GCP_PROJECT'])
region = str(os.environ['mig_region'])
set_mig_size_cf = str(os.environ['mig_size_cf'])
autoscaler_cf = str(os.environ['autoscaler_cf'])
instance_group_manager = str(os.environ['mig_name'])

# Build Parent Path
parent = f'projects/{project}/locations/{region}'

# App Variables
InstanceList = []
CurrentSchedules = []
DefaultMIGSchedule = {}
CustomMIGSchedule = []

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
    global credentials, project, region, instance_group_manager,parent
    service =  discovery.build('cloudscheduler', 'v1', credentials=credentials)

    # Build the request and execute
    request = service.projects().locations().jobs().list(parent=parent)
    ResultList = []
    while True:
        response = request.execute()
        # Itterate over found jobs
        for job in response.get('jobs', []):
            # Filter the results for only those matching this MIG
            if "description" in job:
                aJob = {"name" : job["name"], "schedule" : job["schedule"], "state": job["state"], "description" : job["description"]}
            else:
                aJob = {"name" : job["name"], "schedule" : job["schedule"], "state": job["state"], "description" : ""}

            ResultList.append(aJob)


        request = service.projects().locations().jobs().list_next(previous_request=request, previous_response=response)
        if request is None:
            break

    return ResultList

# DeleteJob
def DeleteSchedule(ScheduleName):
    global credentials, parent
    service =  discovery.build('cloudscheduler', 'v1', credentials=credentials)
    request = service.projects().locations().jobs().delete(name=ScheduleName)
    response = request.execute()
    
    logging.info(response)

# Disable Schedule
def ToggleSchedule(JobName,NewState):
    global credentials
    service = discovery.build('cloudscheduler', 'v1beta1', credentials=credentials)
    job_body = {
        "name" : JobName
    }

    # If NewState is Pause
    if NewState == 'PAUSE':
        request = service.projects().locations().jobs().pause(name=JobName, body=job_body)
    else:
        request = service.projects().locations().jobs().resume(name=JobName, body=job_body)

    # Run the Request
    response = request.execute()
    logging.info(response)

# Create Schedule
def CreateSchedule(ScheduleName,Schedule,TargetSize):
    global set_mig_size_cf ,credentials, project, region, instance_group_manager,parent
    service =  discovery.build('cloudscheduler', 'v1', credentials=credentials)

    # Encode Body
    message = '{"IGM": "'+instance_group_manager+'","Region" : "' + region + '", "NewSize" : ' + TargetSize + '}'
    body = message.encode('utf-8')
    b64_body = base64.b64encode(body)

    # Build the request and execute
    job_body = {
        "schedule" : Schedule,
        "name" : parent + "/jobs/" + ScheduleName,
        "description" : str(TargetSize),
        "timeZone" : "America/Metlakatla",
        "httpTarget" : {
            "uri" : set_mig_size_cf,
            "httpMethod" : "POST",
            "body" : str(b64_body, "utf-8")
        }
    }

    request = service.projects().locations().jobs().create(parent=parent, body=job_body)
    response = request.execute()

    logging.info(response)

# Update Schedule
def UpdateSchedule(JobName,Schedule,State,TargetSize=0):
    global set_mig_size_cf ,credentials, project, region, instance_group_manager, parent, autoscaler_cf
    service =  discovery.build('cloudscheduler', 'v1', credentials=credentials)

    # If this is for customer schedule run below, else update default
    if DefaultMIGSchedule['name'] != JobName:
        # Encode Body
        message = '{"IGM": "'+instance_group_manager+'","Region" : "' + region + '", "NewSize" : ' + str(TargetSize) + '}'
        body = message.encode('utf-8')
        b64_body = base64.b64encode(body)
        body = str(b64_body, "utf-8")
        uri = set_mig_size_cf
        description = str(TargetSize)
    else:
        # Default Autoscaler
        body = ""
        description= ""
        uri = autoscaler_cf

    # Build the request and execute
    job_body = {
        "schedule" : Schedule,
        "name" : JobName,
        "description" : description,
        "timeZone" : "America/Metlakatla",
        "httpTarget" : {
            "uri" : uri,
            "httpMethod" : "POST",
            "body" : body
        }
    }

    request = service.projects().locations().jobs().patch(name=JobName, body=job_body)
    response = request.execute()

    logging.info(response)

# Toggle Schedule
@app.route("/toggle/", methods=['GET'])
def Toggle():
    # App page to toggle status between Active and paused
    jobToEdit = request.args.get('job')
    jobCurrentState = request.args.get('state')

    # Do the opposite of current
    if jobCurrentState == 'ENABLED':
        ToggleSchedule(jobToEdit,'PAUSE')
    else:
        ToggleSchedule(jobToEdit,'ENABLED')
    return redirect("/")

#Delete Schedule
@app.route("/delete/", methods=['GET'])
def Delete():
    # App Page to delete schedule
    JobToEdit = request.args.get('job')
    DeleteSchedule(JobToEdit)
    return redirect("/")

#Edit Schedule
@app.route("/edit/", methods=['GET','POST'])
def edit():
    global LoggingClient, instance_group_manager, project, region, DefaultMIGSchedule, CustomMIGSchedule, InstanceList, CurrentSchedules
   
    JobToEdit = request.args.get('job')

    ## Itterate through list of jobs to find the relevant one
    EditJob = {}
    for aSchedule in CurrentSchedules:
        #If it matches the parameter pass it to the form to edit
        if aSchedule['name'] == JobToEdit:
            # Found it
            EditJob = aSchedule
    
    # Return the page to edit
    return render_template('index.html',job=EditJob,MIG=instance_group_manager, REGION=region, PROJECT=project,CustomSchedule=CustomMIGSchedule,DefaultSchedule=DefaultMIGSchedule,MIGSIZE=len(InstanceList) )

#Save Schedule
@app.route("/save", methods=['POST'])
def save():
    global instance_group_manager, CustomMIGSchedule
    # Save values of submit
    JobName = request.form['fulljobName']
    if 'size' in request.form:
        MigSize = request.form['size']
    else:
        MigSize = 0
    Schedule = request.form['schedule']

    if 'state' in request.form:
        State = "ENABLED"
    else:
        State = ""

    # First check if this is a new request in which case create new Schedule
    if JobName == "":
        ### Standard format based Job Name
        NewJobName = instance_group_manager.lower() + "_custom" + str(len(CustomMIGSchedule)+1)
        CreateSchedule(ScheduleName=NewJobName,Schedule=Schedule,TargetSize=MigSize)
    else:
        ### Update Job
        UpdateSchedule(JobName=JobName,Schedule=Schedule,State=State,TargetSize=MigSize)
    return redirect("/")


#Main Function handler
@app.route("/", methods=['GET'])
def main():
    global LoggingClient, instance_group_manager, project, region, DefaultMIGSchedule, CustomMIGSchedule, InstanceList, CurrentSchedules
   
    # Main Loop
    ## Get list of instances in MIG
    InstanceList = GetInstanceList()

    ## Get Current schedule for the Autoscaler
    CurrentSchedules = GetCurrentSchedule()

    ## Template Render Values
    targetMIG = "check_sessions-" + instance_group_manager.lower()
    targetMIGcustom = instance_group_manager.lower() + "_custom"

    ## Find Default Scheduler
    for aSchedule in CurrentSchedules:
         JobName = str(aSchedule["name"]).lower()
         if search(targetMIG,JobName):
            DefaultMIGSchedule = aSchedule

    ## Find all custom schedules
    CustomMIGSchedule = []
    for aSchedule in CurrentSchedules:
         JobName = str(aSchedule["name"]).lower()
         print(JobName + " " + targetMIGcustom)
         if search(targetMIGcustom,JobName):
            CustomMIGSchedule.append(aSchedule)

    return render_template('index.html',TargetMIG=targetMIG, CustomMIG = targetMIGcustom, MIG=instance_group_manager, REGION=region, PROJECT=project,CustomSchedule=CustomMIGSchedule,DefaultSchedule=DefaultMIGSchedule,MIGSIZE=len(InstanceList) )



if __name__ == "__main__":
    ## Run APP
    app.run(host='0.0.0.0', port=8080)