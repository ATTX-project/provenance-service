## Provenance Service

Current directory contains:
* provenance-service implementation in `src/prov` folder

VERSION: `0.2`

### Docker container

Using the Graph Manager Service Docker container:
* `docker pull attxproject/provenance-service:dev` in the current folder;
* running the container `docker run -d -p 7030:7030 attxproject/provenance-service:dev` runs the container in detached mode on the `7030` port (production version should have this port hidden);
* using the endpoints `http://localhost:7030/{versionNb}/{endpoint}` or the other listed below.

The version number is specified in `src/prov/app.py` under `version` variable.

## Overview

The Provenance Service registers provenance Document in the Graph Store either via the Message Broker or the REST API. Processing the provenance related information is done asyncronously.

Full information on how to run and work with the Provenance Service available at: https://attx-project.github.io/Service-Provenance.html


## API Endpoints

The Graph Manager REST API has the following endpoints:
* `graph` - interface to the Fuseki Graph Store;
* `prov` - API for registering and retriving provenance;
* `health` - checks if the application is running.

## Develop

### Requirements
1. Python 2.7
2. Gradle 3.0+ https://gradle.org/
3. Pypi Ivy repository either a local one (see https://github.com/linkedin/pygradle/blob/master/docs/pivy-importer.md for more information) or you can deploy your own version using https://github.com/blankdots/ivy-pypi-repo

### Building the Artifact with Gradle

Install [gradle](https://gradle.org/install). The tasks available are listed below:

* do clean build: `gradle clean build`
* see tasks: `gradle tasks --all` and depenencies `gradle depenencies`
* see test coverage `gradle pytest coverage` it will generate a html report in `htmlcov`

### Run without Gradle

To run the server, please execute the following (preferably in a virtual environment):
```
pip install -r pinned.txt
python src/prov/provservice.py server
python src/prov/provservice.py queue
python src/prov/provservice.py consumer
```

For testing purposes the application requires a running Fuseki, RabbitMQ. Also the health endpoint provides information on running services the service has detected: `http://localhost:7030/health`

The Swagger definition lives here:`swagger-provservice.yml`.
