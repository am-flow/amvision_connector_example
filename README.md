# AM-Vision Connector sample code and data

Example code and data files for integration with the AM-Vision API

## Repo contents

- **tutorial_prints** sample data used in the tutorial
- **tutorial_code** sample code used in the tutorial
- **connector** a reference BaseConnector and DemoConnector class

## Tutorial code

To run the sample code, you will need to use python 3 (tested on 3.7), and
you'll need some pip packages installed:

    pip install -r requirements.tutorial.txt

You can now run the simple code from the tutorial:

    python tutorial_code/import_simple.py AMV_URL AMV_TOKEN tutorial_prints/meta.yaml

## Reference connector implementation

The reference connector requires some more pip packages

    pip install -r requirements.connector.txt

The reference connector consists of a Flask server that can listen to webhooks and an efficient
bulk importer. You can run the bulk importer like this:

    python -m connector.importer AMV_URL AMV_TOKEN tutorial_prints/meta.yaml

The connector itself can be run with:

    python -m connector.demo CONN_IP CONN_PORT AMV_URL AMV_TOKEN -p tutorial_prints/meta.yaml

It will listen to webhooks and print notifications to the screen. It will also run the bulk
importer every 30 minutes. The demo connector inherits from a BaseConnector that does most of the 
heavy lifting. You're encouraged to consider subclassing the BaseConnector for your own 
implementation.

Note that the connector will by default use Flask's built in development server. If you install
bjoern (a production WSGI server), that will automatically be used instead.

