#!/bin/sh

#Read inputs from the python file
read inputs

#Split java file name from protein sequence
IFS=' '
read -a outputs <<< "$inputs"
read mainClassName <<< "${outputs[0]}"
read mainArguments <<< "${outputs[1]}"

# check specified class exists
if [ ! -f "src/$mainClassName.java" ]; then
    echo "[ERROR] the file src/$mainClassName.java does not exist."
    exit 1;
fi

# compile the classes
mainClassPackage="uk.ac.ebi.uniprot.dataservice.client.examples"
mainClass="$mainClassPackage.$mainClassName"
classes_dir=classes
mkdir -p $classes_dir

javac -d classes -classpath "lib/*" "src/$mainClassName.java"

# run 
java -classpath "$classes_dir:lib/*" $mainClass $mainArguments
