import os
import subprocess
import requests, sys
import json
import requests as http_req
import xml.etree.ElementTree as ET
from Bio.Seq import Seq
from flask import Flask, request, abort, jsonify

#ns for sbol parsing
ns = {
    "rdf":"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dcterms":"http://purl.org/dc/terms/",
    "prov":"http://www.w3.org/ns/prov#",
    "sbol":"http://sbols.org/v2#",
    "xsd":"http://www.w3.org/2001/XMLSchema#dateTime/",
    "om":"http://www.ontology-of-units-of-measure.org/resource/om-2/",
    "synbiohub":"http://synbiohub.org#",
    "sbh":"http://wiki.synbiohub.org/wiki/Terms/synbiohub#",
    "sybio":"http://www.sybio.ncl.ac.uk#",
    "rdfs":"http://www.w3.org/2000/01/rdf-schema#",
    "ncbi":"http://www.ncbi.nlm.nih.gov#",
    "igem":"http://wiki.synbiohub.org/wiki/Terms/igem#",
    "genbank":"http://www.ncbi.nlm.nih.gov/genbank#",
    "gbconv":"http://sbols.org/genBankConversion#" ,
    "dc":"http://purl.org/dc/elements/1.1/" ,
    "obo":"http://purl.obolibrary.org/obo/"
}

#Protein related terms for sbol parsing
term_list = ['http://identifiers.org/so/SO:0000316',"http://wiki.synbiohub.org/wiki/Terms/igem#feature/cds",
    "http://wiki.synbiohub.org/wiki/Terms/igem#partType/Protein_Domain","http://wiki.synbiohub.org/wiki/Terms/igem#feature/protein",
    "http://identifiers.org/so/SO:0000417","http://wiki.synbiohub.org/wiki/Terms/igem#partType/Coding",
    "http://identifiers.org/so/SO:0001069","http://identifiers.org/so/SO:0000104",
    "http://identifiers.org/so/SO:0000851","http://identifiers.org/so/SO:0000839",
    "http://identifiers.org/so/SO:0001237"]

#Function for checking whether SynBioHub entry is a protein
def find_if_prot(sbol_string, term_list):
    root = ET.fromstring(sbol_string)
    compD = root.find('sbol:ComponentDefinition', ns)

    rolesD = compD.findall('sbol:role',ns)
    for role in rolesD:
        if role.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'] in term_list:
            return True

    seqAs = compD.findall('sbol:sequenceAnnotation', ns)
    for seqA in seqAs:
        SeqA = seqA.find('sbol:SequenceAnnotation', ns)
        rolesA = SeqA.findall('sbol:role', ns)
        for role in rolesA:
            if role.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'] in term_list:
                return True

    return False

#Function for determining if a graphic is present and returning value if so
def find_if_graphic(dataBases):
    for entries in dataBases:
        if entries["type"] == "PDB":
            return entries["id"]

    return ""

################
app = Flask(__name__)

#Retrieve status of plugin
@app.route("/status")
def status():
    return("The Visualisation Test Plugin Flask Server is up and running")

#Determine the type of page the user is viewing
@app.route("/evaluate", methods=["POST", "GET"])
def evaluate():
    data = request.get_json(force=True)
    rdf_type = data['type']

    #The plugin should be implemented if the user is viewing a component
    accepted_types = {'Component'}

    acceptable = rdf_type in accepted_types

    if acceptable:
        #retrieve url for sbol file
        data = request.get_json(force=True)
        url = data['complete_sbol']

        #Retrieve sbol file as string
        resp=http_req.get(url)
        sbol_string=resp.text

        #Check whether a protein
        if(find_if_prot(sbol_string, term_list)):
            return f'The type sent ({rdf_type}) is an accepted type', 200
        else:
            return f'The type sent ({rdf_type}) is NOT an accepted type', 415
    else:
        return f'The type sent ({rdf_type}) is NOT an accepted type', 415

#Retrieve information from UniProt and
@app.route("/run", methods=["POST"])
def run():
    #retrieve url for sbol file
    data = request.get_json(force=True)
    url = data['complete_sbol']

    #Retrieve sbol file as string
    resp=http_req.get(url)
    sbol_string=resp.text

    #Parse for nucleotide sequence
    root = ET.fromstring(sbol_string)
    seq = root.find('sbol:Sequence', ns)
    ele =seq.find('sbol:elements', ns)
    nucSeq = Seq(ele.text)

    #Translate nucleotide sequence into amino acid sequence
    protSeq = str(nucSeq.translate())

    #Run blast
    commandInput = "BlastMod " + protSeq
    subprocess.run(["sh","./runBlast.sh"],text=True,input=commandInput)

    #Retreive accessions
    my_file = open("Results.txt")
    content = my_file.readlines()
    my_file.close()

    #Check whether hits were returned
    if content[0] != "None":
        #Collect necessary information
        full_response = ""
        for access in content:
            requestURL_base = "https://www.ebi.ac.uk/proteins/api/proteins/"
            requestURL = requestURL_base + access[:-1]
            full_response = full_response + "www.uniprot.org/uniprot/" + access[:-1] + "\n"

            r = requests.get(requestURL, headers={ "Accept" : "application/json"})

            if not r.ok:
                r.raise_for_status()
                sys.exit()

            responseBody = r.text
            responseBody = json.loads(responseBody)
            full_response = full_response + responseBody["protein"]["recommendedName"]["fullName"]["value"] + "\n"
            full_response = full_response + responseBody["organism"]["names"][0]["value"] + "\n"
            full_response = full_response + responseBody["references"][0]["citation"]["title"] + "\n"
            for author in responseBody["references"][0]["citation"]["authors"]:
                full_response = full_response + author + ", "
            full_response = full_response[:-2] + "\n"
            full_response = full_response + responseBody["references"][0]["citation"]["publication"]["journalName"] + "\n"
            full_response = full_response +"www.ncbi.nlm.nih.gov/nuccore/" + responseBody["dbReferences"][0]["id"] + "\n"
            graphicCode = find_if_graphic(responseBody["dbReferences"])
            if graphicCode != "":
                full_response = full_response + "cdn.rcsb.org/images/structures/" + graphicCode[1:-1].lower() + "/" + graphicCode.lower()  + "/" + graphicCode.lower() + "_model-1.jpeg" + "\n"
            else:
                full_response = full_response + "\n"
            full_response = full_response + responseBody["sequence"]["sequence"] + "\n"
            full_response = full_response + "\n"
    else:
        full_response = "No Results"

    #Write info to file
    my_file = open("Results.txt","w")
    my_file.write(full_response)
    my_file.close()

    cwd = os.getcwd()
    filename = os.path.join(cwd, "Test.html")

    try:
        with open(filename, 'r') as htmlfile:
            result = htmlfile.read()

        #####################################
        #html stuff goes here
        #####################################


        return result
    except Exception as e:
        print(e)
        abort(400)
