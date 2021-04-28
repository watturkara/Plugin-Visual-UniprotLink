import os
import subprocess
import requests, sys
import json
import requests as http_req
import xml.etree.ElementTree as ET
import hashlib
import traceback
from Bio.Seq import Seq
from flask import Flask, request, abort, jsonify

# ns for sbol parsing
ns = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "sbol": "http://sbols.org/v2#",
    "xsd": "http://www.w3.org/2001/XMLSchema#dateTime/",
    "om": "http://www.ontology-of-units-of-measure.org/resource/om-2/",
    "synbiohub": "http://synbiohub.org#",
    "sbh": "http://wiki.synbiohub.org/wiki/Terms/synbiohub#",
    "sybio": "http://www.sybio.ncl.ac.uk#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "ncbi": "http://www.ncbi.nlm.nih.gov#",
    "igem": "http://wiki.synbiohub.org/wiki/Terms/igem#",
    "genbank": "http://www.ncbi.nlm.nih.gov/genbank#",
    "gbconv": "http://sbols.org/genBankConversion#",
    "dc": "http://purl.org/dc/elements/1.1/",
    "obo": "http://purl.obolibrary.org/obo/",
}

# Protein related terms for sbol parsing
term_list = [
    "http://identifiers.org/so/SO:0000316",
    "http://wiki.synbiohub.org/wiki/Terms/igem#feature/cds",
    "http://wiki.synbiohub.org/wiki/Terms/igem#partType/Protein_Domain",
    "http://wiki.synbiohub.org/wiki/Terms/igem#feature/protein",
    "http://identifiers.org/so/SO:0000417",
    "http://wiki.synbiohub.org/wiki/Terms/igem#partType/Coding",
    "http://identifiers.org/so/SO:0001069",
    "http://identifiers.org/so/SO:0000104",
    "http://identifiers.org/so/SO:0000851",
    "http://identifiers.org/so/SO:0000839",
    "http://identifiers.org/so/SO:0001237",
]

# Function for checking whether SynBioHub entry is a protein
def find_if_prot(sbol_string, term_list):
    root = ET.fromstring(sbol_string)
    compD = root.find("sbol:ComponentDefinition", ns)

    rolesD = compD.findall("sbol:role", ns)
    for role in rolesD:
        if (
            role.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]
            in term_list
        ):
            return True

    seqAs = compD.findall("sbol:sequenceAnnotation", ns)
    for seqA in seqAs:
        SeqA = seqA.find("sbol:SequenceAnnotation", ns)
        rolesA = SeqA.findall("sbol:role", ns)
        for role in rolesA:
            if (
                role.attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"]
                in term_list
            ):
                return True

    return False


# Function for determining if a graphic is present and returning value if so
def find_if_graphic(dataBases):
    for entries in dataBases:
        if entries["type"] == "PDB":
            return entries["id"]

    return ""


# Function to cache previous results for faster loading
def cache_data(page_id, data):
    # Keep past 100 results, replace oldest queries
    files = os.listdir("./cache")
    if len(files) > 100:
        oldest_file = min(files, key=os.path.getctime)
        os.remove(os.path.abspath(oldest_file))
    with open("./cache/" + page_id, "w") as qfile:
        json.dump(data, qfile)


################
app = Flask(__name__)

if not os.path.isdir("./cache"):
    os.mkdir("./cache")


# Retrieve status of plugin
@app.route("/status")
def status():
    return "The Visualisation Test Plugin Flask Server is up and running"


# Determine the type of page the user is viewing
@app.route("/evaluate", methods=["POST", "GET"])
def evaluate():
    data = request.get_json(force=True)
    rdf_type = data["type"]

    # The plugin should be implemented if the user is viewing a component
    accepted_types = {"Component"}

    acceptable = rdf_type in accepted_types

    if acceptable:
        return f"The type sent ({rdf_type}) is an accepted type", 200
    else:
        return f"The type sent ({rdf_type}) is NOT an accepted type", 415


# Retrieve information from UniProt and
@app.route("/run", methods=["POST"])
def run():
    data = request.get_json(force=True)

    url = data["complete_sbol"]

    resp = http_req.get(url)
    sbol_string = resp.text
    cwd = os.getcwd()

    try:
        # Check if page results have been stored. If so, return results
        page_id = hashlib.md5(url.encode()).hexdigest()
        if page_id in os.listdir("./cache"):
            with open("./cache/" + page_id) as qfile:
                full_response = json.load(qfile)
            with open(os.path.join(cwd, "html/Uniprot.html"), "r") as htmlfile:
                result = htmlfile.read()
                result = result.replace(
                    "UNIPROT_BLAST_OUTPUT", json.dumps(full_response)
                )
            return result

        # If the component is a protein, retrieve the nucleotide sequence
        if find_if_prot(sbol_string, term_list):
            root = ET.fromstring(sbol_string)
            seq = root.find("sbol:Sequence", ns)
            ele = seq.find("sbol:elements", ns)
            nucSeq = Seq(ele.text)

            # Translate nucleotide sequence into amino acid sequence
            protSeq = str(nucSeq.translate())

            # Run blast
            subprocess.run(
                ["javac", "-d", "./java/classes", "-classpath", "./java/lib/*", "./java/BlastMod.java"]
            )
            subprocess.run(
                [
                    "java",
                    "-classpath",
                    "./java/classes:./java/lib/*",
                    "uk.ac.ebi.uniprot.dataservice.client.examples.BlastMod",
                    protSeq,
                ]
            )
            # Retreive accessions
            my_file = open("Results.txt")
            content = my_file.readlines()
            my_file.close()

            # Check whether hits were returned
            if content[0] != "None":
                print("finished BLAST")
                # Collect necessary information
                full_response = []
                full_response = {"status": "", "data": []}
                for access in content:
                    requestURL_base = "https://www.ebi.ac.uk/proteins/api/proteins/"
                    accession = access[:-1]
                    requestURL = requestURL_base + accession
                    uniLink = "https://www.uniprot.org/uniprot/" + accession

                    r = requests.get(requestURL, headers={"Accept": "application/json"})

                    if not r.ok:
                        r.raise_for_status()
                        sys.exit()
                    
                    responseBody = r.text
                    responseBody = json.loads(responseBody)

                    # Get protein info
                    protName = responseBody["protein"]["recommendedName"]["fullName"][
                        "value"
                    ]
                    orgName = responseBody["organism"]["names"][0]["value"]
                    protSeq = responseBody["sequence"]["sequence"]

                    # Get publication info
                    title = responseBody["references"][0]["citation"]["title"]
                    authors = []
                    for author in responseBody["references"][0]["citation"]["authors"]:
                        authors.append(author)
                    journal = responseBody["references"][0]["citation"]["publication"][
                        "journalName"
                    ]

                    # Get crossreferences
                    refSet = ["EMBL", "PDB"]
                    references = []
                    seen_type = []
                    for ref in responseBody["dbReferences"]:
                        if ref["type"] in refSet and ref["type"] not in seen_type:
                            seen_type.append(ref["type"])
                            if ref["type"] == "EMBL":
                                references.append(
                                    {
                                        "type": ref["type"],
                                        "id": ref["id"],
                                        "Link": "https://www.ncbi.nlm.nih.gov/nuccore/"
                                        + ref["id"],
                                    }
                                )
                            elif ref["type"] == "PDB":
                                references.append(
                                    {
                                        "type": ref["type"],
                                        "id": ref["id"],
                                        "Link": f"https://www.rcsb.org/structure/{ref['id']}",
                                        "img": "http://cdn.rcsb.org/images/structures/"
                                        + ref["id"][1:-1].lower()
                                        + "/"
                                        + ref["id"].lower()
                                        + "/"
                                        + ref["id"].lower()
                                        + "_model-1.jpeg",
                                    }
                                )
                            else:
                                references.append(
                                    {"type": ref["type"], "id": ref["id"]}
                                )

                    # Add to full_response
                    full_response["data"].append(
                        {
                            "Name": protName,
                            "Organism": orgName,
                            "Publication Title": title,
                            "Authors": ", ".join(authors),
                            "Journal": journal,
                            "Accession ID": accession,
                            "Link": uniLink,
                            "Cross References": references,
                        }
                    )
                
                print("finshed part searching")
                full_response["status"]="success"
                # Cache full response to prevent repeating queries
                cache_data(page_id, full_response)

            else:
                full_response = {"status": "No Results"}
        else:
            full_response = {"status": "Not a protein"}
        # Renders the file if there are no errors
        filename = os.path.join(cwd, "html/Uniprot.html")
        with open(filename, "r") as htmlfile:
            result = htmlfile.read()
        result = result.replace("UNIPROT_BLAST_OUTPUT", json.dumps(full_response))
        return result
    except Exception as e:
        # Renders the error html and prints the traceback
        # to the server if an error occurs
        with open(os.path.join(cwd, "html/error.html"), "r") as htmlfile:
            result = htmlfile.read()
        print(traceback.format_exc())
        return result, 299


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
