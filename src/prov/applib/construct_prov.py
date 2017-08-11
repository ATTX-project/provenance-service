import hashlib
from rdflib import Graph, BNode, Literal, URIRef
from rdflib.namespace import RDF, DCTERMS, XSD
from prov.utils.prefixes import bind_prefix, create_URI, ATTXProv, PROV, ATTXBase, ATTXOnto, PWO
#  , SD
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore


def construct_provenance(prov_Object, payload):
    """Parse Provenance Object and construct Provenance Graph."""
    graph = Graph()
    bind_prefix(graph)
    activityID = ''.join(filter(None, ('activity',
                                str(prov_Object['context']['activityID']))))
    workflowID = ''.join(filter(None, ('workflow',
                                str(prov_Object['context']['workflowID']))))
    # if an activity does not include step ID it is an WorkflowExecution
    if prov_Object['context'].get('stepID'):
        stepID = ''.join(filter(None, ('step',
                                str(prov_Object['context']['stepID']))))
    else:
        stepID = None
    base_ID = "_".join(filter(None, (workflowID, activityID, stepID)))
    workflow_ID = "{0}_{1}".format(workflowID, activityID)
    app_logger.info('Constructed base ID: {0}'.format(base_ID))
    try:
        if prov_Object['activity']['type'] == "DescribeStep":
            prov_graph = prov_dataset(graph, base_ID, prov_Object, payload)
        else:
            prov_graph = prov_activity(graph, base_ID, workflow_ID, prov_Object, payload)
        # store_provenance(prov_graph)
        return prov_graph.serialize(format='turtle')
    except Exception as error:
        app_logger.error('Something is wrong with parsing the prov_Object: {0}'.format(error))


def store_provenance(graph):
    """Store resulting provenance in the Graph Store."""
    storage = GraphStore()
    storage_request = storage.graph_update(ATTXProv, graph)
    return storage_request


def prov_activity(graph, base_ID, workflow_ID, prov_Object, payload):
    """Construct Activity provenance Graph."""
    activity = prov_Object['activity']
    agent_ID = str(prov_Object['agent']['ID'])
    activity_URI = create_URI(ATTXBase, base_ID, agent_ID)
    graph.add((activity_URI, RDF.type, PROV.Activity))
    if activity.get('type'):
        graph.add((activity_URI, RDF.type,
                   create_URI(ATTXOnto, activity['type'])))
        prov_association(graph, activity_URI, prov_Object, workflow_ID)
    else:
        prov_association(graph, activity_URI, prov_Object)
    if activity.get('title'):
        graph.add((activity_URI, DCTERMS.title, Literal(activity['title'])))
    if activity.get('description'):
        graph.add((activity_URI, DCTERMS.description, Literal(activity['description'])))
    prov_time(graph, activity_URI, prov_Object)
    if activity.get('communication'):
        prov_communication(graph, activity_URI, base_ID, prov_Object)
    if prov_Object.get('input'):
        prov_usage(graph, activity_URI, prov_Object['input'], payload)
    if prov_Object.get('output'):
        prov_generation(graph, activity_URI, prov_Object['output'], payload)
    app_logger.info('Constructed provenance for Activity with URI: attx:{0}.' .format(base_ID))
    return graph


def prov_time(graph, activity_URI, prov_Object):
    """Figure out start and end times."""
    activity = prov_Object['activity']
    if activity.get('startTime'):
        graph.add((activity_URI, PROV.startedAtTime, Literal(activity['startTime'], datatype=XSD.dateTime)))
    if activity.get('endTime'):
        graph.add((activity_URI, PROV.endedAtTime, Literal(activity['endTime'], datatype=XSD.dateTime)))
    return graph


def prov_association(graph, activity_URI, prov_Object, workflow_ID=None):
    """Associate an activity with an Agent."""
    bnode = BNode()
    agent = prov_Object['agent']
    agent_URI = create_URI(ATTXBase, agent['ID'])

    graph.add((activity_URI, PROV.wasAssociatedWith, agent_URI))
    graph.add((activity_URI, PROV.qualifiedAssociation, bnode))
    graph.add((bnode, RDF.type, PROV.Association))
    graph.add((bnode, PROV.agent, agent_URI))
    graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, agent['role'])))
    if prov_Object['activity']['type'] == 'WorkflowExecution':
        graph.add((bnode, PROV.hadPlan, create_URI(ATTXBase, workflow_ID)))
    if workflow_ID and prov_Object['context'].get('stepID') and prov_Object['activity']['type'] == 'Step':
        prov_workflow(graph, activity_URI, workflow_ID)
    # information about the agent and the artifact used.
    graph.add((agent_URI, RDF.type, PROV.Agent))
    graph.add((agent_URI, RDF.type, ATTXOnto.Artifact))
    return graph


def prov_workflow(graph, activity_URI, workflow_ID):
    """Generate provenance related workflow."""
    workflowURI = create_URI(ATTXBase, workflow_ID)
    graph.add((workflowURI, RDF.type, PROV.Plan))
    graph.add((workflowURI, RDF.type, ATTXOnto.Workflow))
    graph.add((workflowURI, PWO.hasStep, activity_URI))
    return graph


def prov_communication(graph, activity_URI, base_ID, prov_Object):
    """Communication of an activity with another activity."""
    bnode = BNode()
    communication = prov_Object['activity']['communication']
    for activity in communication:
        key_entity = create_URI(ATTXBase, base_ID, activity['agent'])
        graph.add((activity_URI, PROV.qualifiedCommunication, bnode))
        graph.add((bnode, RDF.type, PROV.Communication))
        graph.add((bnode, PROV.activity, key_entity))
        graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, activity['role'])))
        for key in activity['input']:
            graph.add((key_entity, RDF.type, PROV.Activity))
            communication_entity = URIRef("{0}_{1}".format(key_entity, hashlib.md5(str(key)).hexdigest()))
            graph.add((key_entity, PROV.used, communication_entity))
            if activity['input'][key].get('role'):
                bnode_usage = BNode()
                role_URI = create_URI(ATTXBase, "used_{0}".format(activity['input'][key]['role']), hashlib.md5(str(key)).hexdigest())
                graph.add((key_entity, PROV.qualifiedUsage, bnode_usage))
                graph.add((bnode_usage, RDF.type, PROV.Usage))
                graph.add((bnode_usage, PROV.entity, communication_entity))
                graph.add((bnode_usage, PROV.hadRole, role_URI))

            # graph.add((communication_entity, RDF.type, PROV.Entity))
    return graph


def prov_usage(graph, activity_URI, input_Object, payload):
    """Create qualified Usage if possible."""
    bnode = BNode()
    for key in input_Object:
        key_entity = create_URI(ATTXBase, "used_{0}".format(key),
                                hashlib.md5(str(payload[key])).hexdigest())
        graph.add((activity_URI, PROV.used, key_entity))
        if input_Object[key].get('role'):
            graph.add((activity_URI, PROV.qualifiedUsage, bnode))
            graph.add((bnode, RDF.type, PROV.Usage))
            graph.add((bnode, PROV.entity, key_entity))
            graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, input_Object[key]['role'])))

        graph.add((key_entity, RDF.type, PROV.Entity))
        graph.add((key_entity, DCTERMS.source, Literal(str(payload[key]))))
    return graph


def prov_generation(graph, activity_URI, output_Object, payload):
    """Create qualified Usage if possible."""
    bnode = BNode()
    for key in output_Object:
        key_entity = create_URI(ATTXBase, "generated_{0}".format(key),
                                hashlib.md5(str(payload[key])).hexdigest())
        graph.add((activity_URI, PROV.generated, key_entity))
        if output_Object[key].get('role'):
            graph.add((activity_URI, PROV.qualifiedGeneration, bnode))
            graph.add((bnode, RDF.type, PROV.Generation))
            graph.add((bnode, PROV.entity, key_entity))
            graph.add((bnode, PROV.hadRole, create_URI(ATTXBase, output_Object[key]['role'], hashlib.md5(str(payload[key])).hexdigest())))

        graph.add((key_entity, RDF.type, PROV.Entity))
        graph.add((key_entity, DCTERMS.source, Literal(str(payload[key]))))
    return graph


def prov_dataset(graph, base_ID, prov_Object, payload):
    """Describe dataset provenance."""
    output_Object = prov_Object['output']
    agent_ID = str(prov_Object['agent']['ID'])
    activity_URI = create_URI(ATTXBase, base_ID, agent_ID)
    prov_generation(graph, activity_URI, output_Object, payload)
    for key in output_Object:
        key_entity = create_URI(ATTXBase, "generated_{0}".format(key),
                                hashlib.md5(str(payload[key])).hexdigest())
        graph.add((key_entity, RDF.type, ATTXOnto.Dataset))
        graph.add((key_entity, RDF.type, PROV.Entity))
        if type(payload[key]) is dict:
            for value in payload[key]:
                graph.add((key_entity, create_URI(ATTXBase, value), Literal(str(payload[key][value]))))
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
