from flask import Flask, request, abort, jsonify
import os

app = Flask(__name__)

@app.route("/status")
def status():
    return("The Visualisation Test Plugin Flask Server is up and running")

@app.route("/evaluate", methods=["POST", "GET"])
def evaluate():
    return("The type sent is an accepted type")

@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(force=True)
    
    top_level_url = data['top_level']
    complete_sbol = data['complete_sbol']
    instance_url = data['instanceUrl']
    size = data['size']
    rdf_type = data['type']
    shallow_sbol = data['shallow_sbol']
    
    url = complete_sbol.replace('/sbol','')
      
    cwd = os.getcwd()
    filename = os.path.join(cwd, "Test.html")
    
    try:
        with open(filename, 'r') as htmlfile:
            result = htmlfile.read()
            
        #put in the url, uri, and instance given by synbiohub
        result = result.replace("URL_REPLACE", url)
        result = result.replace("URI_REPLACE", top_level_url)
        result = result.replace("INSTANCE_REPLACE", instance_url)
           
        result = result.replace("REQUEST_REPLACE", str(data))
            
        return result
    except Exception as e:
        print(e)
        abort(400)
