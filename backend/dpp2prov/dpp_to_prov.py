from boto3 import Session
from datapackage import Package
import os
from rdflib import BNode, Graph, Literal, Namespace, RDF, URIRef, plugin
from rdflib.namespace import XSD
from rdflib.serializer import Serializer
from requests import get
import simplejson as json
from yaml import safe_load, dump

from dpp2prov.configuration import get_bcodmo_office_uri, get_dpp2prov_bucket_name
from dpp2prov.dpp2prov_logging import setup_logging

# Setup logger
logger = setup_logging(__name__)

redmine_uri = "https://d2rq.bco-dmo.org/id/redmine/"
bcodmo_uri =  "http://lod.bco-dmo.org/id/"

dcterms = Namespace("http://purl.org/dc/terms/")
plan = Namespace("http://purl.org/net/p-plan#")
prov = Namespace("http://www.w3.org/ns/prov#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
schema = Namespace("http://schema.org/")
odo = Namespace("http://ocean-data.org/schema/")
redmine = Namespace(redmine_uri)

def to_prov(dataset_id, version_id, rdf_format=None):
    logger.info(f'Got dataset, version and RDF format: {dataset_id}:{version_id}:{rdf_format}')
    
    if rdf_format is None:
        rdf_format = 'turtle'
        
    g = Graph()
    # Setup namespaces
    g.bind("dcterms", dcterms)
    g.bind("prov", prov)
    g.bind("plan", plan)
    g.bind("rdfs", rdfs)
    g.bind("schema", schema)
    g.bind("xsd", XSD)

    # Establish the BCO-DMO URI
    bcodmo_office_uri = get_bcodmo_office_uri()
    bcodmo_office = URIRef(bcodmo_office_uri)
        
    # Prepare the S3 object names
    bucket = get_dpp2prov_bucket_name()
    root_path = dataset_id + "/" + version_id + "/data/"
    pipeline_path = root_path + "pipeline-spec.yaml"
    data_pkg_path = root_path + "datapackage.json"
    pipeline_url = "s3://" + bucket + "/" + pipeline_path
    data_pkg_url = "s3://" + bucket + "/" + data_pkg_path
    
    # Establish an S3 session
    session = Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )
    s3 = session.resource('s3')

    # Load the pipeline YAML
    workflow = None
    yaml_file = get_s3_object(s3, bucket, pipeline_path)
    generatedTime = yaml_file['last_modified']
    yaml_data = safe_load(yaml_file['data'])

    # ignore the name of the pipeline
    for key, workflow in yaml_data.items():
        break
    
    pipeline_name = workflow['title']
    pipeline_desc = workflow['description']

    # PROV
    bundle = BNode()
    g.add((bundle, RDF.type, prov.Bundle))
    g.add((bundle, rdfs.isDefinedBy, bundle))
    g.add((bundle, prov.generatedAtTime, Literal(generatedTime, datatype=XSD.dateTime)))

    # Entity - Pipeline
    pipeline_spec = BNode()
    g.add((pipeline_spec, rdfs.isDefinedBy, bundle))
    g.add((pipeline_spec, RDF.type, prov.Plan))
    g.add((pipeline_spec, RDF.type, prov.Collection))
    g.add((pipeline_spec, RDF.type, schema.DigitalDocument))
    g.add((pipeline_spec, schema.name, Literal(pipeline_name, datatype=XSD.string)))
    g.add((pipeline_spec, schema.description, Literal(pipeline_desc, datatype=XSD.string)))
    g.add((pipeline_spec, schema.contentUrl, Literal(pipeline_url, datatype=XSD.anyURI)))
    g.add((pipeline_spec, schema.encodingFormat, Literal("application/x-yaml", datatype=XSD.token)))
    
    # Look for the Data Manager in the properties of the workflow, just in case
    data_mgr = find_data_mgr(workflow, g, bundle)

    # Add any unknown properties
    for key in workflow:
        if key not in ['title', 'description', 'pipeline']:
            pipeline_property = BNode()
            g.add((pipeline_property, rdfs.isDefinedBy, bundle))
            g.add((pipeline_spec, plan.isVariableOfPlan, pipeline_property))
            g.add((pipeline_property, RDF.type, plan.Variable))
            g.add((pipeline_property, rdfs.label, Literal(key, datatype=XSD.token)))
            g.add((pipeline_property, RDF.value, Literal(dump(workflow[key], default_flow_style=True, default_style='"'), datatype=odo.yamlLiteral)))

    # Entity - Redmine Issue
    if 'redmineIssueNumber' in workflow:
        redmine_issue_uri = URIRef(redmine_uri + "issue/" + workflow['redmineIssueNumber'])
        g.add((pipeline_spec, prov.wasInfluencedBy, redmine_issue_uri))
        generate_identifier(g, bundle, redmine_issue_uri, workflow['redmineIssueNumber'], scheme=None, id_class=odo.RedmineIssueIdentifier)

    # Entity - Data Submission
    if 'submissionId' in workflow:
        submission = BNode()
        g.add((submission, rdfs.isDefinedBy, bundle))
        g.add((submission, RDF.type, prov.Collection))
        generate_identifier(g, bundle, submission, workflow['submissionId'], scheme=None, id_class=odo.SubmissionIdentifier)
        g.add((pipeline_spec, prov.wasInfluencedBy, submission))

    # Activity - Created pipeline
    created_pipeline = BNode()
    g.add((created_pipeline, rdfs.isDefinedBy, bundle))
    g.add((created_pipeline, RDF.type, prov.Activity))
    g.add((created_pipeline, RDF.type, schema.CreateAction))
    g.add((created_pipeline, prov.generated, pipeline_spec))
    qualified_creation = BNode()
    g.add((qualified_creation, rdfs.isDefinedBy, bundle))
    g.add((qualified_creation, RDF.type, prov.Association))
    g.add((created_pipeline, prov.qualifiedAssociation, qualified_creation))
    g.add((qualified_creation, prov.hadRole, odo.BcoDmoDataManagerRole))
    g.add((qualified_creation, prov.hadPlan, pipeline_spec))
    g.add((pipeline_spec, prov.wasGeneratedBy, created_pipeline))

    # Activity - Executed Pipeline
    executed_pipeline = BNode()
    g.add((executed_pipeline, rdfs.isDefinedBy, bundle))
    g.add((executed_pipeline, RDF.type, prov.Activity))
    g.add((executed_pipeline, RDF.type, schema.PlayAction))
    g.add((executed_pipeline, prov.hadPlan, pipeline_spec))
    g.add((executed_pipeline, prov.used, pipeline_spec))
    g.add((executed_pipeline, prov.wasInformedBy, created_pipeline))
    qualified_execution = BNode()
    g.add((qualified_execution, rdfs.isDefinedBy, bundle))
    g.add((qualified_execution, RDF.type, prov.Association))
    g.add((executed_pipeline, prov.qualifiedAssociation, qualified_execution))
    g.add((qualified_execution, prov.hadRole, odo.BcoDmoDataManagerRole))
    g.add((qualified_execution, prov.hadPlan, pipeline_spec))

    # Entity - Laminar
    if 'version' in workflow:
        laminar = BNode()
        g.add((laminar, rdfs.isDefinedBy, bundle))
        g.add((laminar, RDF.type, schema.SoftwareSourceCode))
        g.add((laminar, RDF.type, prov.Entity))
        g.add((laminar, schema.name, Literal("Laminar", datatype=XSD.string)))
        g.add((laminar, schema.version, Literal(workflow['version'], datatype=XSD.token)))
        g.add((created_pipeline, prov.used, laminar))
        g.add((executed_pipeline, prov.used, laminar))

    # Agent - Data Manager
    dm_delegation = BNode()
    g.add((dm_delegation, rdfs.isDefinedBy, bundle))
    g.add((dm_delegation, RDF.type, prov.Delegation))
    g.add((dm_delegation, prov.agent, bcodmo_office))
    g.add((dm_delegation, prov.hadRole, odo.BcoDmoDataManagerRole))
    g.add((dm_delegation, prov.hadActivity, created_pipeline))
    g.add((dm_delegation, prov.hadActivity, executed_pipeline))
    
    # Keep track of last step so we can preserve the order
    last_step = None
    for order, step in enumerate(workflow['pipeline']):

        # Find the Data Manager
        if data_mgr is None:
            data_mgr = find_data_mgr(step['parameters'], g, bundle)

        # Entity - Processor Step
        prov_step = BNode()
        g.add((prov_step, rdfs.isDefinedBy, bundle))
        g.add((prov_step, RDF.type, plan.Step))
        g.add((prov_step, rdfs.label, Literal(step['run'], datatype=XSD.token)))
        g.add((prov_step, plan.isStepOfPlan, pipeline_spec))
        # for easier SPARQL, store the order of the step as 'rdf:value'
        g.add((prov_step, RDF.value, Literal(order, datatype=XSD.integer)))
        # Entity - Processor Step Input
        for name in step['parameters']:
            var = BNode()
            g.add((var, rdfs.isDefinedBy, bundle))
            g.add((prov_step, plan.hasInputVar, var))
            g.add((var, RDF.type, plan.Variable))
            g.add((var, rdfs.label, Literal(name, datatype=XSD.token)))
            # default_flow_style=True, default_style='"'
            g.add((var, RDF.value, Literal(dump(step['parameters'][name], default_flow_style=True, default_style='"'), datatype=odo.yamlLiteral)))

        # Let steps know which other steps precedes them
        if last_step is not None:
            g.add((prov_step, plan.isPrecededBy, last_step))
        last_step = prov_step

    # Agent - Data Manager
    g.add((bundle, prov.wasAttributedTo, data_mgr))
    g.add((pipeline_spec, prov.wasAttributedTo, data_mgr))
    g.add((data_mgr, RDF.type, prov.Person))
    g.add((data_mgr, prov.qualifiedDelegation, dm_delegation))
    g.add((created_pipeline, prov.wasAssociatedWith, data_mgr))
    g.add((qualified_creation, prov.agent, data_mgr))
    g.add((executed_pipeline, prov.wasAssociatedWith, data_mgr))
    g.add((qualified_execution, prov.agent, data_mgr))

    # Entity - Data Package
    data_pkg = BNode()
    g.add((data_pkg, rdfs.isDefinedBy, bundle))
    g.add((data_pkg, RDF.type, prov.Entity))
    g.add((data_pkg, RDF.type, schema.DigitalDocument))
    g.add((data_pkg, prov.wasGeneratedBy, executed_pipeline))
    g.add((data_pkg, prov.wasAttributedTo, data_mgr))
    g.add((data_pkg, schema.contentUrl, Literal(data_pkg_url, datatype=XSD.anyURI)))
    g.add((data_pkg, schema.encodingFormat, Literal("application/json", datatype=XSD.token)))
    
    fdp = get_s3_object(s3, bucket, data_pkg_path)
    fdp_json = json.loads(fdp['data'])

    package = Package(fdp_json)
    for i in range(len(package.resource_names)):
        resource = package.get_resource(package.resource_names[i])

        # Entity - Processed Data
        new_data = BNode()
        g.add((new_data, rdfs.isDefinedBy, bundle))
        g.add((new_data, RDF.type, prov.Entity))
        g.add((new_data, RDF.type, schema.DataDownload))
        g.add((new_data, prov.wasGeneratedBy, executed_pipeline))
        g.add((new_data, prov.wasAttributedTo, data_mgr))
        g.add((new_data, schema.name, Literal(root_path + resource.descriptor['name'], datatype=XSD.string)))
        g.add((new_data, schema.contentUrl, Literal(root_path + resource.descriptor['path'], datatype=XSD.anyURI)))
        g.add((new_data, schema.encodingFormat, Literal(resource.descriptor['format'], datatype=XSD.token)))

        # store connection between raw and new
        if 'dpp:streamedFrom' in resource.descriptor.keys():
            raw_data = BNode()
            g.add((raw_data, rdfs.isDefinedBy, bundle))
            g.add((raw_data, RDF.type, prov.Entity))
            g.add((raw_data, RDF.type, schema.DataDownload))
            g.add((created_pipeline, prov.used, raw_data))
            g.add((raw_data, schema.contentUrl, Literal(resource.descriptor['dpp:streamedFrom'], datatype=XSD.anyURI)))
            g.add((new_data, prov.wasDerivedFrom, raw_data))
            g.add((new_data, prov.hadPrimarySource, raw_data))
            g.add((new_data, prov.wasRevisionOf, raw_data))

    # Send the provenance
    if rdf_format is 'json-ld':
        return g.serialize(format='json-ld', indent=2).decode("utf-8")
    return g.serialize(format=rdf_format).decode("utf-8")


# Get an S3 object
def get_s3_object(s3, bucket, objectname):
    obj = s3.Object(bucket, objectname)
    return {
        'data': obj.get()['Body'].read(),
        'last_modified': obj.last_modified
    }


# Find a data manager in some dictionary
def find_data_mgr(data_dict, graph, bundle):
    if 'data_manager' in data_dict and 'orcid' in data_dict['data_manager']:
        dm_name = None
        if 'name' in data_dict['data_manager']:
            dm_name = data_dict['data_manager']['name']
        return get_data_mgr_resource(graph, bundle, data_dict['data_manager']['orcid'], dm_name)
    return None


# get the RDF resource for a Data Manager by the given ORCID
def get_data_mgr_resource(graph, bundle, orcid, name=None):
    has_orcid = orcid is not None and len(orcid) > 0
    dm_lookup_url = "https://lod.bco-dmo.org/sparql?query=PREFIX+rdf%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%0D%0APREFIX+rdfs%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0D%0APREFIX+owl%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2002%2F07%2Fowl%23%3E%0D%0APREFIX+arpfo%3A+%3Chttp%3A%2F%2Fvocab.ox.ac.uk%2Fprojectfunding%23%3E%0D%0APREFIX+dc%3A+%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%3E%0D%0APREFIX+dcat%3A+%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Fdcat%23%3E%0D%0APREFIX+dcterms%3A+%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Fterms%2F%3E%0D%0APREFIX+foaf%3A+%3Chttp%3A%2F%2Fxmlns.com%2Ffoaf%2F0.1%2F%3E%0D%0APREFIX+geo%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2003%2F01%2Fgeo%2Fwgs84_pos%23%3E%0D%0APREFIX+geosparql%3A+%3Chttp%3A%2F%2Fwww.opengis.net%2Font%2Fgeosparql%23%3E%0D%0APREFIX+odo%3A+%3Chttp%3A%2F%2Focean-data.org%2Fschema%2F%3E%0D%0APREFIX+participation%3A+%3Chttp%3A%2F%2Fpurl.org%2Fvocab%2Fparticipation%2Fschema%23%3E%0D%0APREFIX+prov%3A+%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Fprov%23%3E%0D%0APREFIX+rs%3A+%3Chttp%3A%2F%2Fjena.hpl.hp.com%2F2003%2F03%2Fresult-set%23%3E%0D%0APREFIX+schema%3A+%3Chttp%3A%2F%2Fschema.org%2F%3E%0D%0APREFIX+sd%3A+%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Fsparql-service-description%23%3E%0D%0APREFIX+sf%3A+%3Chttp%3A%2F%2Fwww.opengis.net%2Font%2Fsf%23%3E%0D%0APREFIX+skos%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2004%2F02%2Fskos%2Fcore%23%3E%0D%0APREFIX+time%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2006%2Ftime%23%3E%0D%0APREFIX+void%3A+%3Chttp%3A%2F%2Frdfs.org%2Fns%2Fvoid%23%3E%0D%0APREFIX+xsd%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2001%2FXMLSchema%23%3E%0D%0ASELECT+DISTINCT+%3Fperson+WHERE+%7B+%3Fperson+odo%3Aidentifier+%3Fid+.+%3Fid+odo%3AidentifierScheme+odo%3AIdentifierScheme_ORCID+.+%3Fid+odo%3AidentifierValue+%22" + orcid + "%22%5E%5Exsd%3Atoken+%7D&output=json"
    dm_response = get(dm_lookup_url, verify=False)
    dm_sparql_results = dm_response.json()

    for result in dm_sparql_results['results']['bindings']:
        # return the first one
        return URIRef(result['person']['value'])

    # return BNode is no DM was found
    dm = BNode()
    g.add((dm, rdfs.isDefinedBy, bundle))
    if name is not None:
        graph.add((dm, rdfs.label, Literal(name, datatype=XSD.string)))
    # add the associated ORCID to the DM bnode
    if has_orcid:
        generate_identifier(graph, bundle, dm, orcid, scheme=odo.IdentifierScheme_ORCID)
    return dm


# generate an Identifier
def generate_identifier(graph, bundle, resource, identifier, scheme=None, id_class=odo.Identifier):
    id = BNode()
    graph.add((resource, odo.identifier, id))
    graph.add((id, RDF.type, id_class))
    if scheme is not None:
        graph.add((id, odo.identifierScheme, scheme))
    graph.add((id, odo.identifierValue, Literal(identifier, datatype=XSD.token)))
