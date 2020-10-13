from flask import Response
import requests
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google.cloud import monitoring_v3
import logging
import os

# Build Credentials
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)
project = os.environ['GCP_PROJECT']


#Function Add Instance to MIG
def ResizeMig(instance_group_manager, region, NewSize):
    global service, credentials, project
    request = service.regionInstanceGroupManagers().resize(project=project, region=region, instanceGroupManager=instance_group_manager, size=NewSize)
    response = request.execute()
    logging.info("Setting %s MIG to size %s",str(instance_group_manager),str(NewSize))
    return response

# Main Function
def Main(request):

    # Get value from request
    request_json = request.get_json(silent=True)
    request_args = request.args

    ## Get IGM
    if request_json and 'IGM' in request_json:
        IGM = str(request_json['IGM'])
    elif request_args and 'IGM' in request_args:
        IGM = str(request_args['IGM'])
    else: 
        IGM = ""

    ## Get Region
    if request_json and 'Region' in request_json:
        Region = str(request_json['Region'])
    elif request_args and 'Region' in request_args:
        Region = str(request_args['Region'])
    else: 
        Region = ""

     ## Get New Size
    if request_json and 'NewSize' in request_json:
        NewSize = int(request_json['NewSize'])
    elif request_args and 'NewSize' in request_args:
        NewSize = int(request_args['NewSize'])
    else: 
        NewSize = ""

    if (IGM == "" or Region == "" or NewSize == ""):
        return Response("Error:missing required fields: IGM Region NewSize.", status=400, mimetype='text/html')
    else:
        Outcome = ResizeMig(instance_group_manager=IGM, region=Region, NewSize=NewSize)
        return (Outcome)