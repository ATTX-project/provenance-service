import hashlib
from rdflib import Graph, BNode, Literal, URIRef
from rdflib.namespace import RDF, DCTERMS, XSD
from prov.utils.prefixes import bind_prefix, create_URI, ATTXProv, PROV, ATTXBase, ATTXOnto, PWO
#  , SD
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
    base_ID = "_".join(filter(None, (workflowID, activityID, stepID)))
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
    agentID = str(provObject['agent']['ID'])
    activityURI = create_URI(ATTXBase, base_ID, agentID)
    graph.add((activityURI, RDF.type, PROV.Activity))
    if activity.get('type'):
        graph.add((activityURI, RDF.type,
                   create_URI(ATTXOnto, activity['type'].title())))
        prov_association(graph, activityURI, provObject, workflow_ID)
    else:
        prov_association(graph, activityURI, provObject)
    if activity.get('title'):
        graph.add((activityURI, DCTERMS.title, Literal(activity['title'])))
    if activity.get('description'):
        graph.add((activityURI, DCTERMS.description, Literal(activity['description'])))
    prov_time(graph, activityURI, provObject)
    if activity.get('communication'):
        prov_communication(graph, activityURI, base_ID, provObject)
    if provObject.get('input'):
        prov_usage(graph, activityURI, provObject['input'], payload)
    if provObject.get('output'):
        prov_generation(graph, activityURI, provObject['output'], payload)
    app_logger.info('Constructed provenance for Activity with URI: attx:{0}.' .format(base_ID))
    return graph


def prov_time(graph, activityURI, provObject):
    """Figure out start and end times."""
    activity = provObject['activity']
    if activity.get('startTime'):
        graph.add((activityURI, PROV.startedAtTime, Literal(activity['startTime'], datatype=XSD.dateTime)))
    if activity.get('endTime'):
        graph.add((activityURI, PROV.endedAtTime, Literal(activity['endTime'], datatype=XSD.dateTime)))
    return graph


def prov_association(graph, activityURI, provObject, workflow_ID=None):
    """Associate an activity with an Agent."""
    bnode = BNode()
    agent = provObject['agent']
    agent_URI = create_URI(ATTXBase, agent['ID'])

    graph.add((activityURI, PROV.wasAssociatedWith, agent_URI))
    graph.add((activityURI, PROV.qualifiedAssociation, bnode))
    graph.add((bnode, RDF.type, PROV.Association))
    graph.add((bnode, PROV.agent, agent_URI))
    graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, agent['role'])))
    if provObject['activity']['type'] == 'WorkflowExecution':
        graph.add((bnode, PROV.hadPlan, create_URI(ATTXBase, workflow_ID)))
    if workflow_ID and provObject['context'].get('stepID') and provObject['activity']['type'] == 'Step':
        prov_workflow(graph, activityURI, workflow_ID)
    # information about the agent and the artifact used.
    graph.add((agent_URI, RDF.type, PROV.Agent))
    graph.add((agent_URI, RDF.type, ATTXOnto.Artifact))
    return graph


def prov_workflow(graph, activityURI, workflow_ID):
    """Generate provenance related workflow."""
    workflowURI = create_URI(ATTXBase, workflow_ID)
    graph.add((workflowURI, RDF.type, PROV.Plan))
    graph.add((workflowURI, RDF.type, ATTXOnto.Workflow))
    graph.add((workflowURI, PWO.hasStep, activityURI))
    return graph


def prov_communication(graph, activityURI, base_ID, provObject):
    """Communication of an activity with another activity."""
    bnode = BNode()
    communication = provObject['activity']['communication']
    for activity in communication:
        key_entity = create_URI(ATTXBase, base_ID, activity['agent'])
        graph.add((activityURI, PROV.qualifiedCommunication, bnode))
        graph.add((bnode, RDF.type, PROV.Communication))
        graph.add((bnode, PROV.activity, key_entity))
        graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, activity['role'].title())))
        for key in activity['input']:
            graph.add((key_entity, RDF.type, PROV.Activity))
            communication_entity = URIRef("{0}_{1}".format(key_entity, hashlib.md5(key).hexdigest()))
            graph.add((key_entity, PROV.used, communication_entity))
            if activity['input'][key].get('role'):
                bnode_usage = BNode()
                graph.add((key_entity, PROV.qualifiedUsage, bnode_usage))
                graph.add((bnode_usage, RDF.type, PROV.Usage))
                graph.add((bnode_usage, PROV.entity, communication_entity))
                graph.add((bnode_usage, PROV.hadRole, create_URI(ATTXBase, "used_{0}".format(activity['input'][key]['role']), hashlib.md5(key).hexdigest())))

            # graph.add((communication_entity, RDF.type, PROV.Entity))
    return graph


def prov_usage(graph, activityURI, inputObject, payload):
    """Create qualified Usage if possible."""
    bnode = BNode()
    for key in inputObject:
        key_entity = create_URI(ATTXBase, "used_{0}".format(key),
                                hashlib.md5(payload[key]).hexdigest())
        graph.add((activityURI, PROV.used, key_entity))
        if inputObject[key].get('role'):
            graph.add((activityURI, PROV.qualifiedUsage, bnode))
            graph.add((bnode, RDF.type, PROV.Usage))
            graph.add((bnode, PROV.entity, key_entity))
            graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, inputObject[key]['role'])))

        graph.add((key_entity, RDF.type, PROV.Entity))
        graph.add((key_entity, DCTERMS.source, Literal(str(payload[key]))))
    return graph


def prov_generation(graph, activityURI, outputObject, payload):
    """Create qualified Usage if possible."""
    bnode = BNode()
    for key in outputObject:
        key_entity = create_URI(ATTXBase, "generated_{0}".format(key),
                                hashlib.md5(payload[key]).hexdigest())
        graph.add((activityURI, PROV.generated, key_entity))
        if outputObject[key].get('role'):
            graph.add((activityURI, PROV.qualifiedGeneration, bnode))
            graph.add((bnode, RDF.type, PROV.Generation))
            graph.add((bnode, PROV.entity, key_entity))
            graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, outputObject[key]['role'], hashlib.md5(payload[key]).hexdigest())))

        graph.add((key_entity, RDF.type, PROV.Entity))
        graph.add((key_entity, DCTERMS.source, Literal(str(payload[key]))))
    return graph


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
