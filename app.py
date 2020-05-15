#FLASK_APP=app.py flask run
from flask import Flask, request, abort
from retrieve_html import retrieve_html
import os

app = Flask(__name__)

#flask run --host=0.0.0.0
@app.route("/sankey/status")
def imdoingfine():
    return("Not dead Jet")

@app.route("/sankey/evaluate", methods=["POST", "GET"])
def evalsankey():
    return("Not dead Jet")


@app.route("/sankey/run", methods=["POST"])
def wrapper():
    cwd = os.getcwd()
    filename = os.path.join(cwd, "Test.html")
    
    data = request.json

    url = data['complete_sbol'].replace('/sbol','')
    instance = data['instanceUrl'].replace('/sbol','')
    uri = data['top_level']

    try:
        #obtain the html from the test file
        result = retrieve_html(filename)
        
        #put in the url, uri, and instance given by synbiohub
        result = result.replace("URL_REPLACE", url)
        result = result.replace("URI_REPLACE", uri)
        result = result.replace("INSTANCE_REPLACE", instance)
     
        return result 
    except Exception as e:
        print(e)
        abort(404)
