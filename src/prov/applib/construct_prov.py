from hashlib import md5
from rdflib import Graph, BNode, Literal, URIRef
from rdflib.namespace import RDF, DCTERMS, XSD
from prov.utils.prefixes import bind_prefix, create_uri, ATTXProv, PROV, ATTXBase, ATTXOnto, PWO
from prov.utils.logs import app_logger
from prov.applib.graph_store import GraphStore
from prov.utils.queue import init_celery
from prov.utils.broker import broker

app = init_celery(broker['user'], broker['pass'], broker['host'])


@app.task(name="construct.provenance", max_retries=5)
def prov_task(prov_object, payload):
    """Parse Provenance Object and construct Provenance Graph."""
    prov = Provenance(prov_object, payload)
    prov._construct_provenance()


class Provenance(object):
    """Provenance Object class."""

    def __init__(self, prov_object, payload):
        """Initalize provenance class."""
        self.graph = Graph()
        self.prov_object = prov_object
        self.payload = payload

    def _construct_provenance(self):
        """Parse Provenance Object and construct Provenance Graph."""
        bind_prefix(self.graph)
        try:
            activity_id = ''.join(filter(None, ('activity',
                                         str(self.prov_object['context']['activityID']))))
            workflow_id = ''.join(filter(None, ('workflow',
                                         str(self.prov_object['context']['workflowID']))))
            # if an activity does not include step ID it is an WorkflowExecution
            if self.prov_object['context'].get('stepID'):
                step_id = ''.join(filter(None, ('step',
                                         str(self.prov_object['context']['stepID']))))
            else:
                step_id = None
            base_uri = "_".join(filter(None, (workflow_id, activity_id, step_id)))
            wf_base_uri = "{0}_{1}".format(workflow_id, activity_id)
            app_logger.info('Constructed base ID: {0}'.format(base_uri))
            if self.prov_object['activity']['type'] == "DescribeStepExecution":
                prov_graph = self._prov_dataset(base_uri)
            else:
                prov_graph = self._prov_activity(base_uri, wf_base_uri)
            self._store_provenance(prov_graph.serialize(format='turtle'))
        except Exception as error:
            app_logger.error('Something is wrong with parsing the prov_object: {0}'.format(error))
            raise error
            # return error.message
        else:
            return prov_graph.serialize(format='turtle')

    def _store_provenance(self):
        """Store resulting provenance in the Graph Store."""
        # We need to store provenance in a separate graph for each context
        # And why not in the global Provenance graph
        storage = GraphStore()
        storage_request = storage._graph_add(ATTXProv, self.graph)
        return storage_request

    def _prov_activity(self, base_uri, wf_base_uri):
        """Construct Activity provenance Graph."""
        activity = self.prov_object['activity']
        agent_id = str(self.prov_object['agent']['ID'])
        act_uri = create_uri(ATTXBase, base_uri, agent_id)
        self.graph.add((act_uri, RDF.type, PROV.Activity))
        if activity.get('type'):
            self.graph.add((act_uri, RDF.type,
                            create_uri(ATTXOnto, activity['type'])))
            self._prov_association(act_uri, wf_base_uri)
        else:
            self._prov_association(act_uri)
        if activity.get('title'):
            self.graph.add((act_uri, DCTERMS.title, Literal(activity['title'])))
        if activity.get('description'):
            self.graph.add((act_uri, DCTERMS.description, Literal(activity['description'])))
        if activity.get('status'):
            self.graph.add((act_uri, ATTXOnto.hasStatus, Literal(activity['status'])))
        if activity.get('configuration'):
            self.graph.add((act_uri, ATTXOnto.hasConfig, Literal(activity['configuration'])))
        self._prov_time(act_uri)
        if activity.get('communication'):
            self._prov_communication(act_uri, wf_base_uri, base_uri)
        if self.prov_object.get('input'):
            self._prov_usage(act_uri, self.prov_object['input'])
        if self.prov_object.get('output'):
            self._prov_generation(act_uri, self.prov_object['output'])
        app_logger.info('Constructed provenance for Activity with URI: attx:{0}.' .format(base_uri))
        # The return is not really needed
        # return graph

    def _prov_time(self, act_uri):
        """Figure out start and end times."""
        activity = self.prov_object['activity']
        if activity.get('startTime'):
            self.graph.add((act_uri, PROV.startedAtTime, Literal(activity['startTime'], datatype=XSD.dateTime)))
        if activity.get('endTime'):
            self.graph.add((act_uri, PROV.endedAtTime, Literal(activity['endTime'], datatype=XSD.dateTime)))
        # The return is not really needed
        # return graph

    def _prov_association(self, act_uri, wf_base_uri=None):
        """Associate an activity with an Agent."""
        agent = self.prov_object['agent']
        agent_URI = create_uri(ATTXBase, agent['ID'])
        role_uri = create_uri(ATTXBase, agent['role'])
        association_uri = create_uri(ATTXBase, "association", md5(str(agent_URI + role_uri + self.prov_object['activity']['type'])).hexdigest())

        self.graph.add((act_uri, PROV.wasAssociatedWith, agent_URI))
        self.graph.add((act_uri, PROV.qualifiedAssociation, association_uri))
        self.graph.add((association_uri, RDF.type, PROV.Association))
        self.graph.add((association_uri, PROV.agent, agent_URI))
        self.graph.add((association_uri, PROV.hadRole, role_uri))
        if self.prov_object['activity']['type'] == 'WorkflowExecution':
            self.graph.add((association_uri, PROV.hadPlan, create_uri(ATTXBase, wf_base_uri)))
        if wf_base_uri and self.prov_object['context'].get('stepID') and self.prov_object['activity']['type'] == 'StepExecution':
            self._prov_workflow(act_uri, wf_base_uri)
        # information about the agent and the artifact used.
        self.graph.add((agent_URI, RDF.type, PROV.Agent))
        self.graph.add((agent_URI, RDF.type, ATTXOnto.Artifact))
        # information about the Role
        self.graph.add((role_uri, RDF.type, PROV.Role))
        # The return is not really needed
        # return graph

    def _prov_workflow(self, act_uri, wf_base_uri):
        """Generate provenance related workflow."""
        workflow_uri = create_uri(ATTXBase, wf_base_uri)
        self.graph.add((workflow_uri, RDF.type, PROV.Plan))
        self.graph.add((workflow_uri, RDF.type, ATTXOnto.Workflow))
        self.graph.add((workflow_uri, PWO.hasStep, act_uri))
        # The return is not really needed
        # return graph

    def _prov_communication(self, act_uri, wf_base_uri, base_uri):
        """Communication of an activity with another activity."""
        bnode = BNode()
        communication = self.prov_object['activity']['communication']
        for activity in communication:
            key_entity = create_uri(ATTXBase, base_uri, activity['agent'])
            sender_role_uri = create_uri(ATTXBase, activity['role'])
            sender_agent_uri = create_uri(ATTXBase, activity['agent'])

            self.graph.add((act_uri, PROV.qualifiedCommunication, bnode))
            self.graph.add((bnode, RDF.type, PROV.Communication))
            self.graph.add((bnode, PROV.activity, key_entity))
            self.graph.add((bnode, PROV.hadRole, sender_role_uri))
            # information about the agent and the artifact used.
            self.graph.add((key_entity, RDF.type, PROV.Activity))
            self.graph.add((key_entity, PROV.wasAssociatedWith, sender_agent_uri))
            self.graph.add((sender_agent_uri, RDF.type, PROV.Agent))
            self.graph.add((sender_agent_uri, RDF.type, ATTXOnto.Artifact))
            # information about the Role
            self.graph.add((sender_role_uri, RDF.type, PROV.Role))
            for key in activity['input']:
                communication_entity = URIRef("{0}_{1}".format(key_entity, md5(str(key['key'])).hexdigest()))
                self.graph.add((key_entity, PROV.used, communication_entity))
                if key.get('role'):
                    bnode_usage = BNode()
                    receiver_role_uri = create_uri(ATTXBase, wf_base_uri, key['role'])
                    self.graph.add((key_entity, PROV.qualifiedUsage, bnode_usage))
                    self.graph.add((bnode_usage, RDF.type, PROV.Usage))
                    self.graph.add((bnode_usage, PROV.entity, communication_entity))
                    self.graph.add((bnode_usage, PROV.hadRole, receiver_role_uri))
                    self.graph.add((receiver_role_uri, RDF.type, PROV.Role))

                # graph.add((communication_entity, RDF.type, PROV.Entity))
        # The return is not really needed
        # return graph

    def _prov_usage(self, act_uri, input_object):
        """Create qualified Usage if possible."""
        # bnode = BNode()
        for key in input_object:
            key_entity = URIRef("{0}_{1}".format(act_uri, key['key']))
            self.graph.add((act_uri, PROV.used, key_entity))
            if key.get('role'):
                role_uri = create_uri(ATTXBase, key['role'])
                usage_uri = create_uri(ATTXBase, "used", md5(str(key['key'] + role_uri)).hexdigest())
                self.graph.add((act_uri, PROV.qualifiedUsage, usage_uri))
                self.graph.add((usage_uri, RDF.type, PROV.Usage))
                self.graph.add((usage_uri, PROV.entity, key_entity))
                self.graph.add((usage_uri, PROV.hadRole, role_uri))
                self.graph.add((role_uri, RDF.type, PROV.Role))

            self.graph.add((key_entity, RDF.type, PROV.Entity))
            if self.payload.get(key['key']):
                self.graph.add((key_entity, DCTERMS.source, Literal(str(self.payload[key['key']]))))
        # The return is not really needed
        # return graph

    def _prov_generation(self, act_uri, output_object):
        """Create qualified Usage if possible."""
        # bnode = BNode()
        for key in output_object:
            key_entity = URIRef("{0}_{1}".format(act_uri, key['key']))
            self.graph.add((act_uri, PROV.generated, key_entity))
            if key.get('role'):
                role_uri = create_uri(ATTXBase, key['role'])
                generation_uri = create_uri(ATTXBase, "generated", md5(str(key['key'] + role_uri)).hexdigest())
                self.graph.add((act_uri, PROV.qualifiedGeneration, generation_uri))
                self.graph.add((generation_uri, RDF.type, PROV.Generation))
                self.graph.add((generation_uri, PROV.entity, key_entity))
                self.graph.add((generation_uri, PROV.hadRole, role_uri))
                self.graph.add((role_uri, RDF.type, PROV.Role))

            self.graph.add((key_entity, RDF.type, PROV.Entity))
            if self.payload.get(key['key']):
                self.graph.add((key_entity, DCTERMS.source, Literal(str(self.payload[key['key']]))))
        # The return is not really needed
        # return graph

    def _prov_dataset(self, base_uri):
        """Describe dataset provenance."""
        if self.prov_object.get('output'):
            output_object = self.prov_object['output']
            agent_id = str(self.prov_object['agent']['ID'])
            act_uri = create_uri(ATTXBase, base_uri, agent_id)
            self._prov_generation(act_uri, output_object)
            self._describe_dataset(output_object, act_uri)
        if self.prov_object.get('input'):
            input_object = self.prov_object['input']
            agent_id = str(self.prov_object['agent']['ID'])
            act_uri = create_uri(ATTXBase, base_uri, agent_id)
            self._prov_usage(act_uri, input_object)
            self._describe_dataset(input_object, act_uri)
        # The return is not really needed
        # return graph

    def _describe_dataset(self, dataset, act_uri):
        """Describe dataset both input and output."""
        for key in dataset:
            key_entity = URIRef("{0}_{1}".format(act_uri, key['key']))
            self.graph.add((key_entity, RDF.type, ATTXOnto.Dataset))
            self.graph.add((key_entity, RDF.type, PROV.Entity))
            dataset_key = key["key"]
            if self.payload.get(dataset_key) and type(self.payload[dataset_key]) is dict:
                self.graph.add((key_entity, DCTERMS.source, Literal(str(self.payload[dataset_key]))))
                for value in self.payload[dataset_key]:
                    self.graph.add((key_entity, create_uri(ATTXBase, value), Literal(str(self.payload[dataset_key][value]))))
            elif self.payload.get(dataset_key) and type(self.payload[dataset_key]) is str:
                self.graph.add((key_entity, DCTERMS.source, Literal(str(self.payload[dataset_key]))))
        # The return is not really needed
        # return graph
