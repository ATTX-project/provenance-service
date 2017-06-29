# provenance-service

## Building and Running the application

### Requirements
1. Python 2.7
2. Gradle 3.0+ https://gradle.org/
3. Pypi Ivy repository either a local one (see https://github.com/linkedin/pygradle/blob/master/docs/pivy-importer.md for more information) or you can deploy your own version using https://github.com/blankdots/ivy-pypi-repo


### Building the application

After all the requirements are satisfied in the root directory run `gradle build`

### Running the application

To use the deployable artifact after build run `./build/deployable/bin/gunicorn prov.webapi:provservice`

To deploy the artifact on your a server unzip `build/distributions/provenance-service-1.0.tar.gz` on one's server and run using `./gunicorn webapp.webapi:webapp` (the options for gunicorn can be added to command such as port number `./build/deployable/bin/gunicorn prov.webapi:provservice -b 127.0.0.1:4300` )
