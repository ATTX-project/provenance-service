import hashlib
from rdflib import Graph, BNode, Literal, URIRef
from rdflib.namespace import RDF, DCTERMS, XSD
from prov.utils.prefixes import bind_prefix, create_URI, ATTXProv, PROV, ATTXBase, ATTXOnto, PWO
from prov.utils.logs import app_logger
from prov.utils.graph_store import GraphStore
from prov.utils.queue import init_celery
from prov.utils.broker import broker

app = init_celery(broker['user'], broker['pass'], broker['host'])


@app.task(name="construct.provenance", max_retries=5)
def construct_provenance(prov_Object, payload):
    """Parse Provenance Object and construct Provenance Graph."""
    graph = Graph()
    bind_prefix(graph)
    try:
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
        base_URI = "_".join(filter(None, (workflowID, activityID, stepID)))
        workflow_base_URI = "{0}_{1}".format(workflowID, activityID)
        app_logger.info('Constructed base ID: {0}'.format(base_URI))
        if prov_Object['activity']['type'] == "DescribeStepExecution":
            prov_graph = prov_dataset(graph, base_URI, prov_Object, payload)
        else:
            prov_graph = prov_activity(graph, base_URI, workflow_base_URI, prov_Object, payload)
        store_provenance(prov_graph.serialize(format='turtle'))
    except Exception as error:
        app_logger.error('Something is wrong with parsing the prov_Object: {0}'.format(error))
        raise error
        # return error.message
    else:
        return prov_graph.serialize(format='turtle')


def store_provenance(graph):
    """Store resulting provenance in the Graph Store."""
    # We need to store provenance in a separate graph for each context
    # And why not in the global Provenance graph
    storage = GraphStore()
    storage_request = storage.graph_add(ATTXProv, graph)
    return storage_request


def prov_activity(graph, base_URI, workflow_base_URI, prov_Object, payload):
    """Construct Activity provenance Graph."""
    activity = prov_Object['activity']
    agent_ID = str(prov_Object['agent']['ID'])
    activity_URI = create_URI(ATTXBase, base_URI, agent_ID)
    graph.add((activity_URI, RDF.type, PROV.Activity))
    if activity.get('type'):
        graph.add((activity_URI, RDF.type,
                   create_URI(ATTXOnto, activity['type'])))
        prov_association(graph, activity_URI, prov_Object, workflow_base_URI)
    else:
        prov_association(graph, activity_URI, prov_Object)
    activity.get('title') and graph.add((activity_URI, DCTERMS.title, Literal(activity['title'])))
    activity.get('description') and graph.add((activity_URI, DCTERMS.description, Literal(activity['description'])))
    activity.get('status') and graph.add((activity_URI, ATTXOnto.hasStatus, Literal(activity['status'])))
    activity.get('configuration') and graph.add((activity_URI, ATTXOnto.hasConfig, Literal(activity['configuration'])))
    prov_time(graph, activity_URI, prov_Object)
    activity.get('communication') and prov_communication(graph, activity_URI, workflow_base_URI, base_URI, prov_Object)
    prov_Object.get('input') and prov_usage(graph, activity_URI, prov_Object['input'], payload)
    prov_Object.get('output') and prov_generation(graph, activity_URI, prov_Object['output'], payload)
    app_logger.info('Constructed provenance for Activity with URI: attx:{0}.' .format(base_URI))
    # The return is not really needed
    return graph


def prov_time(graph, activity_URI, prov_Object):
    """Figure out start and end times."""
    activity = prov_Object['activity']
    activity.get('startTime') and graph.add((activity_URI, PROV.startedAtTime, Literal(activity['startTime'], datatype=XSD.dateTime)))
    activity.get('endTime') and graph.add((activity_URI, PROV.endedAtTime, Literal(activity['endTime'], datatype=XSD.dateTime)))
    # The return is not really needed
    return graph


def prov_association(graph, activity_URI, prov_Object, workflow_base_URI=None):
    """Associate an activity with an Agent."""
    agent = prov_Object['agent']
    agent_URI = create_URI(ATTXBase, agent['ID'])
    role_URI = create_URI(ATTXBase, agent['role'])
    association_URI = create_URI(ATTXBase, "association", hashlib.md5(str(agent_URI + role_URI + prov_Object['activity']['type'])).hexdigest())

    graph.add((activity_URI, PROV.wasAssociatedWith, agent_URI))
    graph.add((activity_URI, PROV.qualifiedAssociation, association_URI))
    graph.add((association_URI, RDF.type, PROV.Association))
    graph.add((association_URI, PROV.agent, agent_URI))
    graph.add((association_URI, PROV.hadRole, role_URI))
    if prov_Object['activity']['type'] == 'WorkflowExecution':
        graph.add((association_URI, PROV.hadPlan, create_URI(ATTXBase, workflow_base_URI)))
    if workflow_base_URI and prov_Object['context'].get('stepID') and prov_Object['activity']['type'] == 'StepExecution':
        prov_workflow(graph, activity_URI, workflow_base_URI)
    # information about the agent and the artifact used.
    graph.add((agent_URI, RDF.type, PROV.Agent))
    graph.add((agent_URI, RDF.type, ATTXOnto.Artifact))
    # information about the Role
    graph.add((role_URI, RDF.type, PROV.Role))
    # The return is not really needed
    return graph


def prov_workflow(graph, activity_URI, workflow_base_URI):
    """Generate provenance related workflow."""
    workflowURI = create_URI(ATTXBase, workflow_base_URI)
    graph.add((workflowURI, RDF.type, PROV.Plan))
    graph.add((workflowURI, RDF.type, ATTXOnto.Workflow))
    graph.add((workflowURI, PWO.hasStep, activity_URI))
    # The return is not really needed
    return graph


def prov_communication(graph, activity_URI, workflow_base_URI, base_URI, prov_Object):
    """Communication of an activity with another activity."""
    bnode = BNode()
    communication = prov_Object['activity']['communication']
    for activity in communication:
        key_entity = create_URI(ATTXBase, base_URI, activity['agent'])
        sender_role_URI = create_URI(ATTXBase, activity['role'])
        sender_agent_URI = create_URI(ATTXBase, activity['agent'])

        graph.add((activity_URI, PROV.qualifiedCommunication, bnode))
        graph.add((bnode, RDF.type, PROV.Communication))
        graph.add((bnode, PROV.activity, key_entity))
        graph.add((bnode, PROV.hadRole, sender_role_URI))
        # information about the agent and the artifact used.
        graph.add((key_entity, RDF.type, PROV.Activity))
        graph.add((key_entity, PROV.wasAssociatedWith, sender_agent_URI))
        graph.add((sender_agent_URI, RDF.type, PROV.Agent))
        graph.add((sender_agent_URI, RDF.type, ATTXOnto.Artifact))
        # information about the Role
        graph.add((sender_role_URI, RDF.type, PROV.Role))
        for key in activity['input']:
            communication_entity = URIRef("{0}_{1}".format(key_entity, hashlib.md5(str(key['key'])).hexdigest()))
            graph.add((key_entity, PROV.used, communication_entity))
            if key.get('role'):
                bnode_usage = BNode()
                receiver_role_URI = create_URI(ATTXBase, workflow_base_URI, key['role'])
                graph.add((key_entity, PROV.qualifiedUsage, bnode_usage))
                graph.add((bnode_usage, RDF.type, PROV.Usage))
                graph.add((bnode_usage, PROV.entity, communication_entity))
                graph.add((bnode_usage, PROV.hadRole, receiver_role_URI))
                graph.add((receiver_role_URI, RDF.type, PROV.Role))

            # graph.add((communication_entity, RDF.type, PROV.Entity))
    # The return is not really needed
    return graph


def prov_usage(graph, activity_URI, input_Object, payload):
    """Create qualified Usage if possible."""
    # bnode = BNode()
    for key in input_Object:
        key_entity = URIRef("{0}_{1}".format(activity_URI, key['key']))
        graph.add((activity_URI, PROV.used, key_entity))
        if key.get('role'):
            role_URI = create_URI(ATTXBase, key['role'])
            usage_URI = create_URI(ATTXBase, "used", hashlib.md5(str(key['key'] + role_URI)).hexdigest())
            graph.add((activity_URI, PROV.qualifiedUsage, usage_URI))
            graph.add((usage_URI, RDF.type, PROV.Usage))
            graph.add((usage_URI, PROV.entity, key_entity))
            graph.add((usage_URI, PROV.hadRole, role_URI))
            graph.add((role_URI, RDF.type, PROV.Role))

        graph.add((key_entity, RDF.type, PROV.Entity))
        payload.get(key['key']) and graph.add((key_entity, DCTERMS.source, Literal(str(payload[key['key']]))))
    # The return is not really needed
    return graph


def prov_generation(graph, activity_URI, output_Object, payload):
    """Create qualified Usage if possible."""
    # bnode = BNode()
    for key in output_Object:
        key_entity = URIRef("{0}_{1}".format(activity_URI, key['key']))
        graph.add((activity_URI, PROV.generated, key_entity))
        if key.get('role'):
            role_URI = create_URI(ATTXBase, key['role'])
            generation_URI = create_URI(ATTXBase, "generated", hashlib.md5(str(key['key'] + role_URI)).hexdigest())
            graph.add((activity_URI, PROV.qualifiedGeneration, generation_URI))
            graph.add((generation_URI, RDF.type, PROV.Generation))
            graph.add((generation_URI, PROV.entity, key_entity))
            graph.add((generation_URI, PROV.hadRole, role_URI))
            graph.add((role_URI, RDF.type, PROV.Role))

        graph.add((key_entity, RDF.type, PROV.Entity))
        payload.get(key['key']) and graph.add((key_entity, DCTERMS.source, Literal(str(payload[key['key']]))))
    # The return is not really needed
    return graph


def prov_dataset(graph, base_URI, prov_Object, payload):
    """Describe dataset provenance."""
    if prov_Object.get('output'):
        output_Object = prov_Object['output']
        agent_ID = str(prov_Object['agent']['ID'])
        activity_URI = create_URI(ATTXBase, base_URI, agent_ID)
        prov_generation(graph, activity_URI, output_Object, payload)
        describe_dataset(graph, output_Object, activity_URI, payload)
    if prov_Object.get('input'):
        input_Object = prov_Object['input']
        agent_ID = str(prov_Object['agent']['ID'])
        activity_URI = create_URI(ATTXBase, base_URI, agent_ID)
        prov_usage(graph, activity_URI, input_Object, payload)
        describe_dataset(graph, input_Object, activity_URI, payload)
    # The return is not really needed
    return graph


def describe_dataset(graph, dataset, activity_URI, payload):
    """Describe dataset both input and output."""
    for key in dataset:
        key_entity = URIRef("{0}_{1}".format(activity_URI, key['key']))
        graph.add((key_entity, RDF.type, ATTXOnto.Dataset))
        graph.add((key_entity, RDF.type, PROV.Entity))
        dataset_key = key["key"]
        if payload.get(dataset_key) and type(payload[dataset_key]) is dict:
            graph.add((key_entity, DCTERMS.source, Literal(str(payload[dataset_key]))))
            for value in payload[dataset_key]:
                graph.add((key_entity, create_URI(ATTXBase, value), Literal(str(payload[dataset_key][value]))))
        elif payload.get(dataset_key) and type(payload[dataset_key]) is str:
            graph.add((key_entity, DCTERMS.source, Literal(str(payload[dataset_key]))))
    # The return is not really needed
    return graph
