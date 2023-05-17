from processor import *
from QueryProcessor import QueryProcessor
from pandas import DataFrame
from sparql_dataframe import get 
from clean_str import remove_special_chars

class TriplestoreQueryProcessor(QueryProcessor):

    def __init__(self):
        super().__init__()

    def getAllCanvases(self):

        endpoint = self.getDbPathOrUrl()
        query_canvases = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?canvas ?id ?label
        WHERE {
            ?canvas a nikCl:Canvas;
            dc:identifier ?id;
            nikAttr:label ?label.
        }
        """

        df_sparql_getAllCanvases = get(endpoint, query_canvases, True)
        return df_sparql_getAllCanvases

    def getAllCollections(self):

        endpoint = self.getDbPathOrUrl()
        query_collections = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?collection ?id ?label
        WHERE {
           ?collection a nikCl:Collection;
           dc:identifier ?id;
           nikAttr:label ?label .
        }
        """

        df_sparql_getAllCollections = get(endpoint, query_collections, True)
        return df_sparql_getAllCollections

    def getAllManifests(self):

        endpoint = self.getDbPathOrUrl()
        query_manifest = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/>

        SELECT ?manifest ?id ?label
        WHERE {
           ?manifest a nikCl:Manifest ;
           dc:identifier ?id ;
           nikAttr:label ?label .
        }
        """

        df_sparql_getAllManifest = get(endpoint, query_manifest, True)
        return df_sparql_getAllManifest

    def getCanvasesInCollection(self, collectionId: str):

        endpoint = self.getDbPathOrUrl()
        query_canInCol = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/>

        SELECT ?canvas ?id ?label 
        WHERE {
            ?collection a nikCl:Collection ;
            dc:identifier "%s" ;
            nikRel:items ?manifest .
            ?manifest a nikCl:Manifest ;
            nikRel:items ?canvas .
            ?canvas a nikCl:Canvas ;
            dc:identifier ?id ;
            nikAttr:label ?label .
        }
        """ % collectionId

        df_sparql_getCanvasesInCollection = get(endpoint, query_canInCol, True)
        return df_sparql_getCanvasesInCollection

    def getCanvasesInManifest(self, manifestId: str):

        endpoint = self.getDbPathOrUrl()
        query_canInMan = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?canvas ?id ?label
        WHERE {
            ?manifest a nikCl:Manifest ;
            dc:identifier "%s" ;
            nikRel:items ?canvas .
            ?canvas a nikCl:Canvas ;
            dc:identifier ?id ;
            nikAttr:label ?label .
        }
        """ % manifestId

        df_sparql_getCanvasesInManifest = get(endpoint, query_canInMan, True)
        return df_sparql_getCanvasesInManifest


    def getManifestsInCollection(self, collectionId: str):

        endpoint = self.getDbPathOrUrl()
        query_manInCol = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/>  

        SELECT ?manifest ?id ?label
        WHERE {
            ?collection a nikCl:Collection ;
            dc:identifier "%s" ;
            nikRel:items ?manifest .
            ?manifest a nikCl:Manifest ;
            dc:identifier ?id ;
            nikAttr:label ?label .
        }
        """ % collectionId

        df_sparql_getManifestInCollection = get(endpoint, query_manInCol, True)
        return df_sparql_getManifestInCollection
    

    def getEntitiesWithLabel(self, label: str): 
            

        endpoint = self.getDbPathOrUrl()
        query_entityLabel = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/>

        SELECT ?entity ?type ?label ?id
        WHERE {
            ?entity nikAttr:label "%s" ;
            a ?type ;
            nikAttr:label ?label ;
            dc:identifier ?id .
        }
        """ % remove_special_chars(label)

        df_sparql_getEntitiesWithLabel = get(endpoint, query_entityLabel, True)
        return df_sparql_getEntitiesWithLabel
    

    def getEntitiesWithCanvas(self, canvasId: str): 
            
        endpoint = self.getDbPathOrUrl()
        query_entityCanvas = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?id ?label ?type
        WHERE {
            ?entity dc:identifier "%s" ;
            dc:identifier ?id ;
            nikAttr:label ?label ;
            a ?type .
        }
        """ % remove_special_chars(canvasId)

        df_sparql_getEntitiesWithCanvas = get(endpoint, query_entityCanvas, True)
        return df_sparql_getEntitiesWithCanvas
    
    def getEntitiesWithId(self, id: str): 
            
        endpoint = self.getDbPathOrUrl()
        query_entityId = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?id ?label ?type
        WHERE {
            ?entity dc:identifier "%s" ;
            dc:identifier ?id ;
            nikAttr:label ?label ;
            a ?type .
        }
        """ % remove_special_chars(id)

        df_sparql_getEntitiesWithId = get(endpoint, query_entityId, True)
        return df_sparql_getEntitiesWithId
    

    def getAllEntities(self): 
            
        endpoint = self.getDbPathOrUrl()
        query_AllEntities = """
        PREFIX dc: <http://purl.org/dc/elements/1.1/> 
        PREFIX nikAttr: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX nikCl: <https://github.com/n1kg0r/ds-project-dhdk/classes/> 
        PREFIX nikRel: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?entity ?id ?label ?type
        WHERE {
            ?entity dc:identifier ?id ;
                    dc:identifier ?id ;
                    nikAttr:label ?label ;
                    a ?type .
        }
        """ 

        df_sparql_getAllEntities = get(endpoint, query_AllEntities, True)
        return df_sparql_getAllEntities
