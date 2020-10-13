from flask import Flask, jsonify, Response, request
import random
import socket


## Config App
app = Flask(__name__)
SessionCount = random.randint(0,30)
ServerName = socket.gethostname()


# Main Page
@app.route("/", methods=['GET'])
def Main():
    global SessionCount
    # Return current Session Count & Server Name
    returnValue = {}
    returnValue["ServerName"] = ServerName
    returnValue["SessionCount"] = SessionCount
    SessionCount = random.randint(0,30)
    return jsonify(returnValue)

# Increment Value
@app.route("/add", methods=['GET', 'POST'])
def AddSession():
    # Increase Session by default of 1 or optional value
    global SessionCount

    if 'val' in request.args:
        SessionCount += int(request.args['val'])
    else:
        SessionCount += 1
    
    returnValue = {}
    returnValue["ServerName"] = ServerName
    returnValue["SessionCount"] = SessionCount

    return jsonify(returnValue)

# Decrease Value
@app.route("/sub", methods=['GET', 'POST'])
def SubtractSessions():
    # Increase Session by default of 1 or optional value
    global SessionCount

    if 'val' in request.args:
        SessionCount -= int(request.args['val'])
    else:
        SessionCount -= 1
    
    returnValue = {}
    returnValue["ServerName"] = ServerName
    returnValue["SessionCount"] = SessionCount

    return jsonify(returnValue)

# Randomize Value
@app.route("/new", methods=['GET', 'POST'])
def NewSession():
    # Increase Session by default of 1 or optional value
    global SessionCount

    if 'val' in request.args:
        SessionCount = int(request.args['vale'])
    else:
        SessionCount = random.randint(0,20)
    
    returnValue = {}
    returnValue["ServerName"] = ServerName
    returnValue["SessionCount"] = SessionCount

    return jsonify(returnValue)

if __name__ == "__main__":
        ## Run APP
    app.run(host='0.0.0.0', port="8080")