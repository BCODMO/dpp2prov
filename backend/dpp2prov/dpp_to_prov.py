from yaml import load, dump
from rdflib import BNode, Graph, Literal, RDF, URIRef, plugin
from rdflib.namespace import XSD
from rdflib.serializer import Serializer

from dpp2prov.configuration import get_bcodmo_office_uri
from dpp2prov.dpp2prov_logging import setup_logging

logger = setup_logging(__name__)

dcterms = Namespace("http://purl.org/dc/terms/")
prov = Namespace("http://www.w3.org/ns/prov#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
schema = Namespace("http://schema.org/")
odo = Namespace("http://ocean-data.org/schema/")

def to_prov(dataset_id, version_id, rdf_format=None):
    logger.info(f'Got dataset, version and RDF format: {dataset_id}:{version_id}:{rdf_format}')
    
    if rdf_format is None:
        rdf_format = 'turtle'
        
    # Establish the BCO-DMO URI
    bcodmo_office_uri = get_bcodmo_office_uri()
    bcodmo_office = URIRef(bcodmo_office_uri)
        
    # Get the pipeline YAML & datapackage file from S3
    
    # Load the pipeline YAML & datapackage file
    
    # Build the provenance
    g = Graph() 
    
    # Data Manager
    orcid = ""
    data_mgr = get_data_mgr_resource(g, orcid)

    # Setup namespaces
    g.bind("dcterms", dcterms)
    g.bind("prov", prov)
    g.bind("rdfs", rdfs)
    g.bind("schema", schema)
    g.bind("xsd", XSD)
    
    # S3 object created/lastmodified
    generatedTime = ""
    pipeline_name = ""
    pipeline_desc = ""
    pipeline_url = ""
    data_pkg_url = ""
    
    # PROV
    bundle = BNode()
    g.add((bundle, RDF.type, prov.Bundle))
    g.add((bundle, prov.wasAttributedTo, data_mgr))
    g.add((bundle, prov.generatedAtTime Literal(generatedTime, datatype=XSD.dateTime)))
    
    pipeline_spec = BNode()
    g.add((pipeline_spec, rdfs.isDefinedBy, bundle))
    g.add((pipeline_spec, RDF.type, prov.Plan))
    g.add((pipeline_spec, RDF.type, schema.DigitalDocument))
    g.add((pipeline_spec, prov.wasAttributedTo, data_mgr))
    g.add((pipeline_spec, schema.name, Literal(pipeline_name, datatype=XSD.string)))
    g.add((pipeline_spec, schema.description, Literal(pipeline_desc, datatype=XSD.string)))
    g.add((pipeline_spec, schema.contentUrl, Literal(pipeline_url, datatype=XSD.anyURI)))
    g.add((pipeline_spec, schema.encodingFormat, Literal("application/x-yaml", datatype=XSD.token)))
 
    created_pipeline = BNode()
    g.add((created_pipeline, rdfs.isDefinedBy, bundle))
    g.add((created_pipeline, RDF.type, prov.Activity))
    g.add((created_pipeline, prov.generated, pipeline_spec))
    qualified_creation = BNode()
    g.add((created_pipeline, prov.qualifiedAssociation, qualified_creation))
    g.add((qualified_creation, prov.agent, data_mgr)) 
    g.add((qualified_creation, prov.hadRole, odo.BcoDmoDataManagerRole))
    g.add((qualified_creation, prov.hadPlan, pipeline_spec)) 
    g.add((pipeline_spec, prov.wasGeneratedBy, created_pipeline))

    executed_pipeline = BNode()
    g.add((executed_pipeline, rdfs.isDefinedBy, bundle))
    g.add((executed_pipeline, RDF.type, prov.Activity))
    g.add((executed_pipeline, prov.hadPlan, pipeline_spec))
    qualified_execution = BNode()
    g.add((executed_pipeline, prov.qualifiedAssociation, qualified_execution))
    g.add((qualified_execution, prov.agent, data_mgr)) 
    g.add((qualified_execution, prov.hadRole, odo.BcoDmoDataManagerRole))
    g.add((qualified_execution, prov.hadPlan, pipeline_spec)) 
          
    dm_delegation = BNode()
    g.add((dm_delegation, rdfs.isDefinedBy, bundle))
    g.add((data_mgr, RDF.type, prov.Person))
    g.add((data_mgr, prov:qualifiedDelegation, dm_delegation))
    g.add((dm_delegation, RDF.type, prov.Delegation))
    g.add((dm_delegation, prov.agent, bcodmo_office))
    g.add((dm_delegation, prov.hadRole, odo.BcoDmoDataManagerRole))
    g.add((dm_delegation, prov.hadActivity, created_pipeline))
    g.add((dm_delegation, prov.hadActivity, executed_pipeline))
    
    raw_data = BNode()
    g.add((raw_data, rdfs.isDefinedBy, bundle))
    g.add((raw_data, RDF.type, prov.Entity))
    g.add((raw_data, RDF.type, schema.Dataset))
    raw_data_distro = BNode()
    g.add((raw_data, schema.distribution, bundle))
    g.add((raw_data_distro, RDF.type, schema.DataDownload))
    g.add((created_pipeline, prov.used, raw_data))
    # From load step
    raw_data_url = ""
    g.add((raw_data_distro, schema.contentUrl, Literal(raw_data_url, datatype=XSD.anyURI))

    data_pkg = BNode()
    g.add((data_pkg, rdfs.isDefinedBy, bundle))
    g.add((data_pkg, RDF.type, prov.Entity))
    g.add((data_pkg, RDF.type, schema.DigitalDocument))
    g.add((data_pkg, prov.wasGeneratedBy, executed_pipeline))
    g.add((data_pkg, schema.contentUrl, Literal(data_pkg_url, datatype=XSD.anyURI)))
    g.add((data_pkg, schema.encodingFormat, Literal("application/json", datatype=XSD.token)))

    new_data = BNode()
    g.add((new_data, rdfs.isDefinedBy, bundle))
    g.add((new_data, RDF.type, prov.Entity))
    g.add((new_data, RDF.type, schema.DataDownload))
    g.add((new_data, prov.wasGeneratedBy, executed_pipeline))
    g.add((new_data, prov.hadPrimarySource, raw_data))
    g.add((new_data, prov.wasDerivedFrom, raw_data))
    g.add((new_data, schema.contentUrl, Literal(new_data_url, datatype=XSD.anyURI)))
    g.add((new_data, schema.encodingFormat, Literal("text/csv", datatype=XSD.token)))
          
    
    # Send the provenance
    if rdf_format is 'json-ld':
        return g.serialize(format='json-ld', indent=2).decode("utf-8")
    return g.serialize(format=rdf_format).decode("utf-8")


# get the RDF resource for a Data Manager by the given ORCID
def get_data_mgr_resource(graph, orcid):
    has_orcid = orcid is not None and len(orcid) > 0:
        dm_lookup_url = "https://lod.bco-dmo.org/sparql?query=PREFIX+rdf%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%0D%0APREFIX+rdfs%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0D%0APREFIX+owl%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2002%2F07%2Fowl%23%3E%0D%0APREFIX+arpfo%3A+%3Chttp%3A%2F%2Fvocab.ox.ac.uk%2Fprojectfunding%23%3E%0D%0APREFIX+dc%3A+%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%3E%0D%0APREFIX+dcat%3A+%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Fdcat%23%3E%0D%0APREFIX+dcterms%3A+%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Fterms%2F%3E%0D%0APREFIX+foaf%3A+%3Chttp%3A%2F%2Fxmlns.com%2Ffoaf%2F0.1%2F%3E%0D%0APREFIX+geo%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2003%2F01%2Fgeo%2Fwgs84_pos%23%3E%0D%0APREFIX+geosparql%3A+%3Chttp%3A%2F%2Fwww.opengis.net%2Font%2Fgeosparql%23%3E%0D%0APREFIX+odo%3A+%3Chttp%3A%2F%2Focean-data.org%2Fschema%2F%3E%0D%0APREFIX+participation%3A+%3Chttp%3A%2F%2Fpurl.org%2Fvocab%2Fparticipation%2Fschema%23%3E%0D%0APREFIX+prov%3A+%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Fprov%23%3E%0D%0APREFIX+rs%3A+%3Chttp%3A%2F%2Fjena.hpl.hp.com%2F2003%2F03%2Fresult-set%23%3E%0D%0APREFIX+schema%3A+%3Chttp%3A%2F%2Fschema.org%2F%3E%0D%0APREFIX+sd%3A+%3Chttp%3A%2F%2Fwww.w3.org%2Fns%2Fsparql-service-description%23%3E%0D%0APREFIX+sf%3A+%3Chttp%3A%2F%2Fwww.opengis.net%2Font%2Fsf%23%3E%0D%0APREFIX+skos%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2004%2F02%2Fskos%2Fcore%23%3E%0D%0APREFIX+time%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2006%2Ftime%23%3E%0D%0APREFIX+void%3A+%3Chttp%3A%2F%2Frdfs.org%2Fns%2Fvoid%23%3E%0D%0APREFIX+xsd%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2001%2FXMLSchema%23%3E%0D%0ASELECT+DISTINCT+%3Fperson+WHERE+%7B+%3Fperson+odo%3Aidentifier+%3Fid+.+%3Fid+odo%3AidentifierScheme+odo%3AIdentifierScheme_ORCID+.+%3Fid+odo%3AidentifierValue+%22" + orcid + "%22%5E%5Exsd%3Atoken+%7D&output=json"
        dm_response = requests.get(dm_lookup_url)
        dm_sparql_results = dm_response.json()

        for result in dm_sparql_results['results']['bindings']:
            return URIRef(result['person']['value'])
          
    # return BNode is no DM was found
    dm = BNode() 
    # add the associated ORCID to the DM bnode
    if has_orcid:
        id = BNode()
        graph.add((dm, odo.identifier, id))
        graph.add((id, RDF.type, odo.Identifier))
        graph.add((id, odo.identifierScheme, odo.IdentifierScheme_ORCID))
        graph.add((id, odo.identifierValue, Literal(orcid, datatype=XSD.token)))
          
    return dm
