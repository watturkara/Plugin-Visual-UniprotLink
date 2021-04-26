# Plugin-Visual-Test
A very small test plugin to test the visualisation interface is working for SynBioHub. Could be the basis for python based visualisation plugins.

# Install
## Using docker
Run `docker run --publish 8080:5000 --detach --name python-test-plug synbiohub/plugin-visual-test:snapshot`
Check it is up using localhost:8080.

## Using Python
Clone the github repository to your local computer.
Ensure that a java compiler is installed.
In that directory, run `pip install -r requirements.txt` to install the requirements.
Then run `FLASK_APP=app python -m flask run`. 
A flask module will run at localhost:5000/.
