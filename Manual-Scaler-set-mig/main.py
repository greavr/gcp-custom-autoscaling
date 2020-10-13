from flask import Response
import requests
import google.cloud.logging
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google.cloud import monitoring_v3
import logging
import os
import sys

# Build Credentials
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)
project = os.environ['GCP_PROJECT']


#Function Add Instance to MIG
def ResizeMig(instance_group_manager, region, NewSize):
    global service, credentials, project
    logging.info(f"Attempting Resize of {instance_group_manager}, in the {region} region to a new size of {NewSize}")
    try:
        request = service.regionInstanceGroupManagers().resize(project=project, region=region, instanceGroupManager=instance_group_manager, size=NewSize)
        response = request.execute()
        logging.info("Setting %s MIG to size %s",str(instance_group_manager),str(NewSize))
        return response
    except:
        logging.error(sys.exc_info()[1])
        return "Error"

# Main Function
def Main(request):

    # Setup the logger
    LoggingClient = google.cloud.logging.Client()
    LoggingClient.get_default_handler()
    LoggingClient.setup_logging()
    

    # Get value from request
    request_json = request.get_json(silent=True,force=True)
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
        logging.error(f"Missing Params, provided IGM:{IGM} Region:{Region} NewSize={NewSize}")
        return Response("Error:missing required fields: IGM Region NewSize.", status=400, mimetype='text/html')
    else:
        Outcome = ResizeMig(instance_group_manager=IGM, region=Region, NewSize=NewSize)
        return (Outcome)

if __name__ == "__main__":
    Main("")

