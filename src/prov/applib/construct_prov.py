import hashlib
from rdflib import Graph, BNode, Literal, URIRef
from rdflib.namespace import RDF, DCTERMS, XSD
from prov.utils.prefixes import bind_prefix, create_URI, ATTXProv, PROV, ATTXBase, ATTXOnto
# , PWO, SD
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore


def construct_provenance(provObject, payload):
    """Parse Provenance Object and construct Provenance Graph."""
    graph = Graph()
    bind_prefix(graph)
    activityID = ''.join(filter(None, ('activity',
                                str(provObject['context']['activityID']))))
    workflowID = ''.join(filter(None, ('workflow',
                                str(provObject['context']['workflowID']))))
    # if an activity does not include step ID it is an WorkflowExecution
    if provObject['context'].get('stepID'):
        stepID = ''.join(filter(None, ('step',
                                str(provObject['context']['stepID']))))
    else:
        stepID = None
    agentID = str(provObject['agent']['ID'])
    base_ID = "_".join(filter(None, (workflowID, activityID, stepID, agentID)))
    workflow_ID = "{0}_{1}".format(workflowID, activityID)
    app_logger.info('Constructed base ID: {0}'.format(base_ID))
    try:
        prov_graph = prov_activity(graph, base_ID, workflow_ID, provObject, payload)
        # store_provenance(prov_graph)
        return prov_graph.serialize(format='turtle')
    except Exception as error:
        app_logger.error('Something is wrong with parsing the provObject: {0}'.format(error))


def store_provenance(graph):
    """Store resulting provenance in the Graph Store."""
    storage = GraphStore()
    storage_request = storage.graph_update(ATTXProv, graph)
    return storage_request


def prov_activity(graph, base_ID, workflow_ID, provObject, payload):
    """Construct Activity provenance Graph."""
    activity = provObject['activity']
    graph.add((create_URI(ATTXBase, base_ID), RDF.type, PROV.Activity))
    if activity.get('type'):
        graph.add((create_URI(ATTXBase, base_ID), RDF.type,
                   create_URI(ATTXOnto, activity['type'].title())))
        prov_association(graph, base_ID, provObject, workflow_ID)
    else:
        prov_association(graph, base_ID, provObject)
    if activity.get('title'):
        graph.add((create_URI(ATTXBase, base_ID), DCTERMS.title, Literal(activity['title'])))
    if activity.get('description'):
        graph.add((create_URI(ATTXBase, base_ID), DCTERMS.description, Literal(activity['description'])))
    if activity.get('communication'):
        prov_communication(graph, base_ID, provObject)
    if provObject.get('input'):
        prov_usage(graph, base_ID, provObject['input'], payload)
    if provObject.get('output'):
        prov_generation(graph, base_ID, provObject['output'], payload)
    app_logger.info('Constructed provenance for Activity with URI: attx:{0}.' .format(base_ID))
    return graph


def prov_time(graph, base_ID, provObject):
    """Figure out start and end times."""
    activity = provObject['activity']
    if activity.get('startTime'):
        graph.add((create_URI(ATTXBase, base_ID), PROV.startedAtTime, Literal(activity['startTime'], datatype=XSD.dateTime)))
    if activity.get('endTime'):
        graph.add((create_URI(ATTXBase, base_ID), PROV.endedAtTime, Literal(activity['endTime'], datatype=XSD.dateTime)))
    return graph


def prov_association(graph, base_ID, provObject, workflow_ID=None):
    """Associate an activity with an Agent."""
    bnode = BNode()
    agent = provObject['agent']
    agent_URI = create_URI(ATTXBase, agent['ID'])

    graph.add((create_URI(ATTXBase, base_ID), PROV.wasAssociatedWith, agent_URI))
    graph.add((create_URI(ATTXBase, base_ID), PROV.qualifiedAssociation, bnode))
    graph.add((bnode, RDF.type, PROV.Association))
    graph.add((bnode, PROV.agent, agent_URI))
    graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, agent['role'])))
    if workflow_ID:
        graph.add((bnode, PROV.hadPlan, create_URI(ATTXBase, workflow_ID)))

    graph.add((create_URI(ATTXBase, agent['ID']), RDF.type, PROV.Agent))
    # information about the agent and the artifact used.
    # graph.add((create_URI(ATTXBase, agent['ID']), ATTXOnto.usesArtifact, create_URI(ATTXBase, artifact)))
    return graph


def prov_communication(graph, base_ID, provObject):
    """Communication of an activity with another activity."""
    bnode = BNode()
    communication = provObject['activity']['communication']
    for activity in communication:
        key_entity = create_URI(ATTXBase, base_ID, activity['role'])
        graph.add((create_URI(ATTXBase, base_ID), PROV.qualifiedCommunication, bnode))
        graph.add((bnode, RDF.type, PROV.Communication))
        graph.add((bnode, PROV.activity, key_entity))
        graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, activity['role'])))
        for key in activity['input']:
            graph.add((key_entity, RDF.type, PROV.Activity))
            if activity['input'][key].get('role'):
                bnode_usage = BNode()
                communication_entity = URIRef("{0}_{1}".format(key_entity, activity['input'][key]['role']))
                graph.add((key_entity, PROV.qualifiedUsage, bnode_usage))
                graph.add((bnode_usage, RDF.type, PROV.Usage))
                graph.add((bnode_usage, PROV.entity, communication_entity))
                graph.add((bnode_usage, PROV.hadRole, create_URI(ATTXBase, activity['input'][key]['role'])))

                graph.add((communication_entity, RDF.type, PROV.Entity))
    return graph


def prov_usage(graph, base_ID, inputObject, payload):
    """Create qualified Usage if possible."""
    bnode = BNode()
    for key in inputObject:
        key_entity = create_URI(ATTXBase, key,
                                hashlib.md5(payload[key]).hexdigest())
        graph.add((create_URI(ATTXBase, base_ID), PROV.used, key_entity))
        if inputObject[key].get('role'):
            graph.add((create_URI(ATTXBase, base_ID), PROV.qualifiedUsage, bnode))
            graph.add((bnode, RDF.type, PROV.Usage))
            graph.add((bnode, PROV.entity, key_entity))
            graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, inputObject[key]['role'])))

        graph.add((key_entity, RDF.type, PROV.Entity))
        graph.add((key_entity, DCTERMS.source, Literal(payload[key])))
    return graph


def prov_generation(graph, base_ID, outputObject, payload):
    """Create qualified Usage if possible."""
    bnode = BNode()
    for key in outputObject:
        key_entity = create_URI(ATTXBase, key,
                                hashlib.md5(payload[key]).hexdigest())
        graph.add((create_URI(ATTXBase, base_ID), PROV.generated, key_entity))
        if outputObject[key].get('role'):
            graph.add((create_URI(ATTXBase, base_ID), PROV.qualifiedGeneration, bnode))
            graph.add((bnode, RDF.type, PROV.Generation))
            graph.add((bnode, PROV.entity, key_entity))
            graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, outputObject[key]['role'])))

        graph.add((key_entity, RDF.type, PROV.Entity))
        graph.add((key_entity, DCTERMS.source, Literal(payload[key])))
    return graph

# def construct_provenance(provObject):
#     """Construct provenance graph based on request."""
#     graph = Graph()
#     bind_prefix(graph)
#     try:
#         workflow_provenance(graph, strategy)
#         activity_provenance(graph, startTime, endTime, strategy, generatedDataset, usedDatasetList)
#         store_api = "http://{0}:{1}/{2}/data?graph={3}".format(endpoint['host'], endpoint['port'], endpoint['dataset'], ATTXProv)
#         headers = {'Content-Type': 'text/turtle'}
#         result = requests.post(store_api, data=graph.serialize(format='turtle'), headers=headers)
#         app_logger.info('Add to graph store: "{0}" the result of the linking strategy.'.format(ATTXProv))
#         return result.status_code
#     except Exception as error:
#         app_logger.error('Something is wrong: {0}'.format(error))
#         raise falcon.HTTPUnprocessableEntity(
#             'Unprocessable Graph generated by strategy',
#             'Could not update graph store with the graph generated by the strategy.'
#         )


# def activity_provenance(graph, startTime, endTime, strategy, generatedDataset, usedDatasetList=None):
#     """Generate activity related provenance."""
#     bnode = BNode()
#     activity_id = str(random.randint(1e15, 1e16))
#     workflow_id = "_link_{0}".format(strategy)
#
#     graph.add((URIRef("{0}activity{1}".format(ATTXBase, activity_id)), RDF.type, PROV.Activity))
#     graph.add((URIRef("{0}activity{1}".format(ATTXBase, activity_id)), RDF.type, ATTXOnto.WorkflowExecution))
#     graph.add((URIRef("{0}activity{1}".format(ATTXBase, activity_id)), PROV.startedAtTime, Literal(startTime, datatype=XSD.dateTime)))
#     graph.add((URIRef("{0}activity{1}".format(ATTXBase, activity_id)), PROV.endedAtTime, Literal(endTime, datatype=XSD.dateTime)))
#     graph.add((URIRef("{0}activity{1}".format(ATTXBase, activity_id)), PROV.qualifiedAssociation, bnode))
#     graph.add((bnode, RDF.type, PROV.Assocation))
#     graph.add((bnode, PROV.hadPlan, URIRef("{0}workflow{1}".format(ATTXBase, workflow_id))))
#     graph.add((bnode, PROV.agent, URIRef("{0}{1}".format(ATTXBase, agent))))
#     graph.add((URIRef("{0}{1}".format(ATTXBase, agent)), RDF.type, PROV.Agent))
#     # information about the agent and the artifact used.
#     graph.add((URIRef("{0}{1}".format(ATTXBase, agent)), ATTXOnto.usesArtifact, URIRef("{0}{1}".format(ATTXBase, artifact))))
#     if usedDatasetList is not None:
#         for dataset in usedDatasetList:
#             dataset_provenance(graph, dataset, activity_id, "used")
#     dataset_provenance(graph, str(generatedDataset), activity_id, "generated")
#     app_logger.info('Construct activity metadata for Activity: activity{0}.' .format(activity_id))
#     return graph
#
#
# def dataset_provenance(graph, dataset, activityID, datasetType):
#     """Generate datasets associated to the provenance."""
#     graph.add((URIRef(dataset), RDF.type, ATTXOnto.Dataset))
#     graph.add((URIRef(dataset), RDF.type, SD.Dataset))
#     if datasetType == "used":
#         graph.add((URIRef("{0}activity{1}".format(ATTXBase, activityID)), PROV.used, URIRef(dataset)))
#     elif datasetType == "generated":
#         graph.add((URIRef("{0}activity{1}".format(ATTXBase, activityID)), PROV.generated, URIRef(dataset)))
#         graph.add((URIRef(dataset), DC.title, Literal("activity{0} Linking Dataset".format(activityID))))
#         graph.add((URIRef(dataset), DC.description, Literal("Dataset generated from activity".format(activityID))))
#         graph.add((URIRef(dataset), DC.publisher, Literal("ATTX HULib")))
#         # graph.add((URIRef(dataset), DC.source, Literal()))
#         # graph.add((URIRef(dataset), CC.license, ATTXOnto.CC0))
#     return graph
#
#
# def workflow_provenance(graph, strategy):
#     """Generate workflow related provenance."""
#     workflow_id = "_link_{0}".format(strategy)
#     # There will be only one type of workflow and steps. Steps might differ in configuration.
#     graph.add((URIRef("{0}workflow{1}".format(ATTXBase, workflow_id)), RDF.type, ATTXOnto.Workflow))
#     graph.add((URIRef("{0}workflow{1}".format(ATTXBase, workflow_id)), DC.title, Literal("Linking Workflow")))
#     graph.add((URIRef("{0}workflow{1}".format(ATTXBase, workflow_id)), DC.description, Literal("Workflow specific to the link GM API endpoint")))
#     # Add predifined steps for the workflow
#     generate_step(graph, 1, strategy, "Retrieve {0} parameters".format(strategy),
# "Retrieve paramters for the linking for the specified strategy.", workflow_id)
#     generate_step(graph, 2, strategy, "Construct linking graph for {0}".format(strategy), "Generate linking graph based on strategy parameters.", workflow_id)
#     generate_step(graph, 3, strategy, "Add to graph store", "Add generated linking graph by {0} to the graph store.".format(strategy), workflow_id)
#     graph.add((URIRef("{0}step{1}_{2}".format(ATTXBase, 1, strategy)), PWO.hasNextStep, URIRef("{0}step{1}_{2}".format(ATTXBase, 2, strategy))))
#     graph.add((URIRef("{0}step{1}_{2}".format(ATTXBase, 2, strategy)), PWO.hasNextStep, URIRef("{0}step{1}_{2}".format(ATTXBase, 3, strategy))))
#
#     app_logger.info('Construct activity metadata for Workflow: workflow{0} + associated steps.' .format(workflow_id))
#     return graph
#
#
# def generate_step(graph, stepID, strategy, title, description, workflow):
#     """Generate step details."""
#     graph.add((URIRef("{0}step{1}_{2}".format(ATTXBase, stepID, strategy)), RDF.type, ATTXOnto.Step))
#     graph.add((URIRef("{0}step{1}_{2}".format(ATTXBase, stepID, strategy)), DC.title, Literal(title)))
#     graph.add((URIRef("{0}step{1}_{2}".format(ATTXBase, stepID, strategy)), DC.description, Literal(description)))
#     graph.add((URIRef("{0}workflow{1}".format(ATTXBase, workflow)), PWO.hasStep, URIRef("{0}step{1}_{2}".format(ATTXBase, stepID, strategy))))
#     return graph
