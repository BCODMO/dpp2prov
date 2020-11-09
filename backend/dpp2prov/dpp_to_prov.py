from datetime import datetime
from random import randrange

from yaml import load, dump
from rdflib import BNode, Graph, Literal, RDF, URIRef, plugin
from rdflib.namespace import XSD
from rdflib.serializer import Serializer

from dpp2prov.dpp2prov_logging import setup_logging

logger = setup_logging(__name__)


def to_prov(dataset_id, version_id, rdf_format=None):
    logger.info(f'Got dataset, version and RDF format: {dataset_id}:{version_id}:{rdf_format}')
    
    if rdf_format is None:
        rdf_format = 'turtle'
        
    # Get the pipeline YAML & datapackage file from S3
    
    # Load the pipeline YAML & datapackage file
    
    data_mgr = URIRef("")
    generatedTime = ""
    
    # Build the provenance
    g = Graph() 
    
    # Setup namespaces
    dcterms = Namespace("http://purl.org/dc/terms/")
    prov = Namespace("http://www.w3.org/ns/prov#")
    rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    schema = Namespace("http://schema.org/")
    g.bind("dcterms", dcterms)
    g.bind("prov", prov)
    g.bind("rdfs", rdfs)
    g.bind("schema", schema)
    g.bind("xsd", XSD)
    
    # PROV
    bundle = BNode()
    g.add((bundle, RDF.type, "prov:Bundle"))
    g.add((bundle, prov.wasAttributedTo, data_mgr))
    g.add((bundle, prov.generatedAtTime Literal(generatedTime, datatype=XSD.dateTime)))
    
    
    
    # Send the provenance
    if rdf_format is 'json-ld':
        return g.serialize(format='json-ld', indent=2).decode("utf-8")
    return g.serialize(format=rdf_format).decode("utf-8")
    
