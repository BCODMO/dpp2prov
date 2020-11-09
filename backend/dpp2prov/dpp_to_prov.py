from datetime import datetime
from random import randrange

from yaml import load, dump
from rdflib import Graph, Literal, RDF, URIRef, plugin
from rdflib.namespace import XSD
from rdflib.serializer import Serializer

from dpp2prov.dpp2prov_logging import setup_logging

logger = setup_logging(__name__)


def to_prov(dataset_id, version_id, rdf_format=None):
    logger.info(f'Got dataset, version and RDF format: {dataset_id}:{version_id}:{rdf_format}')
    
    if rdf_format is None:
        rdf_format = 'turtle'
        
    # Get the pipeline YAML file from S3
    
    # Load the pipeline YAML
    
    # Build the provenance
    g = Graph()
    # Create an RDF URI node to use as the subject for multiple triples
    donna = URIRef("http://example.org/donna")
    # Add triples using store's add() method.
    g.add((donna, RDF.type, FOAF.Person))
    g.add((donna, FOAF.nick, Literal("donna", lang="ed")))
    g.add((donna, FOAF.name, Literal("Donna Fales")))
    g.add((donna, FOAF.mbox, URIRef("mailto:donna@example.org")))
    # Add another person
    ed = URIRef("http://example.org/edward")
    # Add triples using store's add() method.
    g.add((ed, RDF.type, FOAF.Person))
    g.add((ed, FOAF.nick, Literal("ed", datatype=XSD.string)))
    g.add((ed, FOAF.name, Literal("Edward Scissorhands")))
    g.add((ed, FOAF.mbox, URIRef("mailto:e.scissorhands@example.org")))
    
    # Send the provenance
    return g.serialize(format='n3').decode("utf-8")
    
