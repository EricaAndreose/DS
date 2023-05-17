from sqlite3 import connect
from pandas import read_sql, DataFrame, concat, read_csv, Series, merge
from utils.paths import RDF_DB_URL, SQL_DB_URL
from rdflib import Graph, Literal, URIRef
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from sparql_dataframe import get 
from clean_str import remove_special_chars
from json import load
from utils.CreateGraph import create_Graph
from urllib.parse import urlparse


#NOTE: BLOCK DATA MODEL

class IdentifiableEntity():
    def __init__(self, id:str):
        self.id = id
    def getId(self):
        return self.id


class Image(IdentifiableEntity):
    pass


class Annotation(IdentifiableEntity):
    def __init__(self, id, motivation:str, target:IdentifiableEntity, body:Image):
        self.motivation = motivation
        self.target = target
        self.body = body
        super().__init__(id)
    def getBody(self):
        return self.body
    def getMotivation(self):
        return self.motivation
    def getTarget(self):
        return self.target
    

class EntityWithMetadata(IdentifiableEntity):
    def __init__(self, id, label, title, creators):
        self.label = label 
        self.title = title
        self.creators = list()
        if type(creators) == str:
            self.creators.append(creators)
        elif type(creators) == list:
            self.creators = creators

        super().__init__(id)

    def getLabel(self):
        return self.label
    
    def getTitle(self):
        if self.title:
            return self.title
        else:
            return None
    
    def getCreators(self):
        return self.creators
    

class Canvas(EntityWithMetadata):
    def __init__(self, id:str, label:str, title:str, creators:list[str]):
        super().__init__(id, label, title, creators)

class Manifest(EntityWithMetadata):
    def __init__(self, id:str, label:str, title:str, creators:list[str], items:list[Canvas]):
        super().__init__(id, label, title, creators)
        self.items = items
    def getItems(self):
        return self.items

class Collection(EntityWithMetadata):
    def __init__(self, id:str, label:str, title:str, creators:list[str], items:list[Manifest]):
        super().__init__(id, label, title, creators)
        self.items = items
    def getItems(self):
        return self.items




# NOTE: BLOCK PROCESSORS


class Processor(object):
    def __init__(self):
        self.dbPathOrUrl = ""
    def getDbPathOrUrl(self):
        return self.dbPathOrUrl 
    def setDbPathOrUrl(self, newpath):
        if len(newpath)>=3 and newpath[-3:] == ".db":
            self.dbPathOrUrl = newpath
            return True
        else:
            is_url = urlparse(newpath)
            if all([is_url.scheme, is_url.netloc]):
                self.dbPathOrUrl = newpath
                return True
            else:
                return False


class QueryProcessor(Processor):
    def __init__(self):
        super().__init__()

    def getEntityById(self, entityId: str):
        entityId_stripped = entityId.strip("'")
        db_url = self.getDbPathOrUrl() if len(self.getDbPathOrUrl()) else SQL_DB_URL
        df = DataFrame()
        if db_url == SQL_DB_URL:
            with connect(db_url) as con:
                query = \
                "SELECT *" +\
                " FROM Entity" +\
                " LEFT JOIN Annotation" +\
                " ON Entity.id = Annotation.target" +\
                " WHERE 1=1" +\
                f" AND Entity.id='{entityId_stripped}'"
                df = read_sql(query, con)

        elif db_url == RDF_DB_URL:
            endpoint = 'http://127.0.0.1:9999/blazegraph/sparql'
            query = """
                PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
                PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
                PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

                SELECT ?entity
                WHERE {
                    ?entity ns2:identifier "%s" .
                }
                """ % entityId 

            df = get(endpoint, query, True)
            return df
        return df


class TriplestoreQueryProcessor(QueryProcessor):

    def __init__(self):
        super().__init__()

    def getAllCanvases(self):

        endpoint = self.getDbPathOrUrl()
        query_canvases = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?canvas ?id ?label
        WHERE {
            ?canvas a <https://github.com/n1kg0r/ds-project-dhdk/classes/Canvas>;
            ns2:identifier ?id;
            ns1:label ?label.
        }
        """

        df_sparql_getAllCanvases = get(endpoint, query_canvases, True)
        return df_sparql_getAllCanvases

    def getAllCollections(self):

        endpoint = self.getDbPathOrUrl()
        query_collections = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?collection ?id ?label
        WHERE {
           ?collection a <https://github.com/n1kg0r/ds-project-dhdk/classes/Collection>;
           ns2:identifier ?id;
           ns1:label ?label .
        }
        """

        df_sparql_getAllCollections = get(endpoint, query_collections, True)
        return df_sparql_getAllCollections

    def getAllManifests(self):

        endpoint = self.getDbPathOrUrl()
        query_manifest = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?manifest ?id ?label
        WHERE {
           ?manifest a <https://github.com/n1kg0r/ds-project-dhdk/classes/Manifest>;
           ns2:identifier ?id;
           ns1:label ?label .
        }
        """

        df_sparql_getAllManifest = get(endpoint, query_manifest, True)
        return df_sparql_getAllManifest

    def getCanvasesInCollection(self, collectionId: str):

        endpoint = self.setDbPathOrUrl()
        query_canInCol = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?canvas ?id ?label 
        WHERE {
            ?collection a <https://github.com/n1kg0r/ds-project-dhdk/classes/Collection> ;
            ns2:identifier "%s" ;
            ns3:items ?manifest .
            ?manifest a <https://github.com/n1kg0r/ds-project-dhdk/classes/Manifest> ;
            ns3:items ?canvas .
            ?canvas a <https://github.com/n1kg0r/ds-project-dhdk/classes/Canvas> ;
            ns2:identifier ?id ;
            ns1:label ?label .
        }
        """ % collectionId

        df_sparql_getCanvasesInCollection = get(endpoint, query_canInCol, True)
        return df_sparql_getCanvasesInCollection

    def getCanvasesInManifest(self, manifestId: str):

        endpoint = self.getDbPathOrUrl()
        query_canInMan = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?canvas ?id ?label
        WHERE {
            ?manifest a <https://github.com/n1kg0r/ds-project-dhdk/classes/Manifest> ;
            ns2:identifier "%s" ;
            ns3:items ?canvas .
            ?canvas a <https://github.com/n1kg0r/ds-project-dhdk/classes/Canvas> ;
            ns2:identifier ?id ;
            ns1:label ?label .
        }
        """ % manifestId

        df_sparql_getCanvasesInManifest = get(endpoint, query_canInMan, True)
        return df_sparql_getCanvasesInManifest


    def getManifestsInCollection(self, collectionId: str):

        endpoint = self.getDbPathOrUrl()
        query_manInCol = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?manifest ?id ?label
        WHERE {
            ?collection a <https://github.com/n1kg0r/ds-project-dhdk/classes/Collection> ;
            ns2:identifier "%s" ;
            ns3:items ?manifest .
            ?manifest a <https://github.com/n1kg0r/ds-project-dhdk/classes/Manifest> ;
            ns2:identifier ?id ;
            ns1:label ?label .
        }
        """ % collectionId

        df_sparql_getManifestInCollection = get(endpoint, query_manInCol, True)
        return df_sparql_getManifestInCollection
    

    def getEntitiesWithLabel(self, label: str): 
            

        endpoint = self.getDbPathOrUrl()
        query_entityLabel = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?entity ?type ?label ?id
        WHERE {
            ?entity ns1:label "%s" ;
            a ?type ;
            ns1:label ?label ;
            ns2:identifier ?id .
        }
        """ % remove_special_chars(label)

        df_sparql_getEntitiesWithLabel = get(endpoint, query_entityLabel, True)
        return df_sparql_getEntitiesWithLabel
    

    def getEntitiesWithCanvas(self, canvasId: str): 
            
        endpoint = self.getDbPathOrUrl()
        query_entityCanvas = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?id ?label ?type
        WHERE {
            ?entity ns2:identifier "%s" ;
            ns2:identifier ?id ;
            ns1:label ?label ;
            a ?type .
        }
        """ % remove_special_chars(canvasId)

        df_sparql_getEntitiesWithCanvas = get(endpoint, query_entityCanvas, True)
        return df_sparql_getEntitiesWithCanvas
    
    def getEntitiesWithId(self, id: str): 
            
        endpoint = self.getDbPathOrUrl()
        query_entityId = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?id ?label ?type
        WHERE {
            ?entity ns2:identifier "%s" ;
            ns2:identifier ?id ;
            ns1:label ?label ;
            a ?type .
        }
        """ % remove_special_chars(id)

        df_sparql_getEntitiesWithId = get(endpoint, query_entityId, True)
        return df_sparql_getEntitiesWithId
    

    def getAllEntities(self): 
            
        endpoint = self.getDbPathOrUrl()
        query_AllEntities = """
        PREFIX ns1: <https://github.com/n1kg0r/ds-project-dhdk/attributes/> 
        PREFIX ns2: <http://purl.org/dc/elements/1.1/> 
        PREFIX ns3: <https://github.com/n1kg0r/ds-project-dhdk/relations/> 

        SELECT ?entity ?id ?label ?type
        WHERE {
            ?entity ns2:identifier ?id ;
                    ns2:identifier ?id ;
                    ns1:label ?label ;
                    a ?type .
        }
        """ 

        df_sparql_getAllEntities = get(endpoint, query_AllEntities, True)
        return df_sparql_getAllEntities




class RelationalQueryProcessor(Processor):          
    def getAllAnnotations(self):
        with connect(self.getDbPathOrUrl()) as con:
            q1="SELECT * FROM Annotation;" 
            q1_table = read_sql(q1, con)
            return q1_table 
              
    def getAllImages(self):
        with connect(self.getDbPathOrUrl()) as con:
          q2="SELECT * FROM Image;" 
          q2_table = read_sql(q2, con)
          return q2_table       
    def getAnnotationsWithBody(self, bodyId:str):
        with connect(self.getDbPathOrUrl())as con:
            q3 = f"SELECT* FROM Annotation WHERE body = '{bodyId}'"
            q3_table = read_sql(q3, con)
            return q3_table         
    def getAnnotationsWithBodyAndTarget(self, bodyId:str,targetId:str):
        with connect(self.getDbPathOrUrl())as con:
            q4 = f"SELECT* FROM Annotation WHERE body = '{bodyId}' AND target = '{targetId}'"
            q4_table = read_sql (q4, con)
            return q4_table         
    def getAnnotationsWithTarget(self, targetId:str):#I've decided not to catch the empty string since in this case a Dataframe is returned, witch is okay
        with connect(self.getDbPathOrUrl())as con:
            q5 = f"SELECT* FROM Annotation WHERE target = '{targetId}'"
            q5_table = read_sql(q5, con)
            return q5_table  
    def getEntitiesWithCreator(self, creatorName):
        with connect(self.getDbPathOrUrl())as con:
             q6 = "SELECT Entity.entityid, Entity.id, Creators.creator, Entity.title FROM Entity LEFT JOIN Creators ON Entity.entityId == Creators.entityId WHERE creator = '" + creatorName +"'"
             result = read_sql(q6, con)
             return result
    def getEntitiesWithTitle(self,title):
        with connect(self.getDbPathOrUrl())as con:
             q6 = "SELECT Entity.entityid, Entity.id, Creators.creator, Entity.title FROM Entity LEFT JOIN Creators ON Entity.entityId == Creators.entityId WHERE title = '" + title +"'"
             result = read_sql(q6, con)  
             return result
    def getEntities(self):
        with connect(self.getDbPathOrUrl())as con:
             q7 = "SELECT Entity.entityid, Entity.id, Creators.creator, Entity.title FROM Entity LEFT JOIN Creators ON Entity.entityId == Creators.entityId"
             result = read_sql(q7, con) 
             return result 
        


class AnnotationProcessor(Processor):
    def __init__(self):
        pass
    def uploadData(self, path:str): 
        try:
            annotations = read_csv(path, 
                                    keep_default_na=False,
                                    dtype={
                                        "id": "string",
                                        "body": "string",
                                        "target": "string",
                                        "motivation": "string"
                                    })
            annotations_internalId = []
            for idx, row in annotations.iterrows():
                annotations_internalId.append("annotation-" +str(idx))
            annotations.insert(0, "annotationId", Series(annotations_internalId, dtype = "string"))
            
            image = annotations[["body"]]
            image = image.rename(columns={"body": "id"})
            image_internalId = []
            for idx, row in image.iterrows():
                image_internalId.append("image-" +str(idx))
            image.insert(0, "imageId", Series(image_internalId, dtype = "string"))

            with connect(self.getDbPathOrUrl()) as con:
                annotations.to_sql("Annotation", con, if_exists="replace", index=False)
                image.to_sql("Image", con, if_exists="replace", index=False)

            return True
        
        except Exception as e:
            print(str(e))
            return False

class MetadataProcessor(Processor):
    def __init__(self):
        pass
    def uploadData(self, path:str):
        try: 
            entityWithMetadata= read_csv(path, 
                                    keep_default_na=False,
                                    dtype={
                                        "id": "string",
                                        "title": "string",
                                        "creator": "string"
                                    })
            
            metadata_internalId = []
            for idx, row in entityWithMetadata.iterrows():
                metadata_internalId.append("entity-" +str(idx))
            entityWithMetadata.insert(0, "entityId", Series(metadata_internalId, dtype = "string"))
            creator = entityWithMetadata[["entityId", "creator"]]
            #I recreate entityMetadata since, as I will create a proxy table, I will have no need of
            #coloumn creator
            entityWithMetadata = entityWithMetadata[["entityId", "id", "title"]]
            

            for idx, row in creator.iterrows():
                        for item_idx, item in row.iteritems():
                            if "entity-" in item:
                                entity_id = item
                            if ";" in item:
                                list_of_creators =  item.split(";")
                                creator = creator.drop(idx)
                                new_serie = []
                                for i in range (len(list_of_creators)):
                                    new_serie.append(entity_id)
                                new_data = DataFrame({"entityId": new_serie, "creator": list_of_creators})
                                creator = concat([creator.loc[:idx-1], new_data, creator.loc[idx:]], ignore_index=True)

            with connect(self.getDbPathOrUrl()) as con:
                entityWithMetadata.to_sql("Entity", con, if_exists="replace", index = False)
                creator.to_sql("Creators", con, if_exists="replace", index = False)
            return True
        except Exception as e:
                print(str(e))
                return False



class CollectionProcessor(Processor):

    def __init__(self):
        super().__init__()

    def uploadData(self, path: str):

        try: 

            base_url = "https://github.com/n1kg0r/ds-project-dhdk/"
            my_graph = Graph()
            

            with open(path, mode='r', encoding="utf-8") as jsonfile:
                json_object = load(jsonfile)
            
            #CREATE GRAPH
            if type(json_object) is list: #CONTROLLARE!!!
                for collection in json_object:
                    create_Graph(collection, base_url, my_graph)
            
            else:
                create_Graph(json_object, base_url, my_graph)
            
                    
            #DB UPTDATE
            store = SPARQLUpdateStore()

            endpoint = self.getDbPathOrUrl()

            store.open((endpoint, endpoint))

            for triple in my_graph.triples((None, None, None)):
                store.add(triple)
            store.close()

            with open('grafo.ttl', mode='a', encoding='utf-8') as f:
                f.write(my_graph.serialize(format='turtle'))

            return True
        
        except Exception as e:
            print(str(e))
            return False
        


# NOTE: BLOCK GENERIC PROCESSOR

class GenericQueryProcessor():
    def __init__(self):
        self.queryProcessors = []
    def cleanQueryProcessors(self):
        self.queryProcessors = []
        return True
    def addQueryProcessor(self, processor: QueryProcessor):
        try:
            self.queryProcessors.append(processor)
            return True 
        except Exception as e:
            print(e)
            return False
        
    def getAllAnnotations(self):
        result = []
        for processor in self.queryProcessors:
            try:
                df = processor.getAllAnnotations()
                df = df.reset_index() 

                annotations_list = [
                    Annotation(row['id'], 
                               row['motivation'], 
                               IdentifiableEntity(row['target']), 
                               Image(row['body'])
                               ) for _, row in df.iterrows()
                ]
                result += annotations_list
            except Exception as e:
                print(e)
        return result
    
    
    def getAllCanvas(self):
        result = []
        for processor in self.queryProcessors:
            try:
                df = processor.getAllCanvases()
                df = df.reset_index() 
                
                canvases_list = [
                    Canvas(row['id'],
                               row['label'], 
                               row['title'],
                               []
                               ) for _, row in df.iterrows()
                ] 
                result += canvases_list
            except Exception as e:
                print(e)
        return result
    

    def getAllCollections(self):
        result = []
        for processor in self.queryProcessors:
            try:
                df = processor.getAllCollections()
                df = df.reset_index() 
                
                collections_list = [
                    Collection(row['id'],
                               row['label'],
                               row['collection'],
                               [],
                               [
                                   Manifest('','','',[],Canvas('','','',''))
                                ]
                                ) for _, row in df.iterrows()
                ] 
                result += collections_list
            except Exception as e:
                print(e)
        return result


    def getAllImages(self):
        for processor in self.queryProcessors:
            try:
                processor.getAllImages()
            except Exception as e:
                print(e)
    def getAllManifests(self):
        for processor in self.queryProcessors:
            try:
                processor.getAllManifests()
            except Exception as e:
                print(e)
    def getAnnotationsToCanvas(self):
        for processor in self.queryProcessors:
            try:
                processor.getAnnotationsToCanvas()
            except Exception as e:
                print(e)
    def getAnnotationsToCollection(self):
        for processor in self.queryProcessors:
            try:
                processor.getAnnotationsToCollection()
            except Exception as e:
                print(e)
    def getAnnotationsToManifest(self):
        for processor in self.queryProcessors:
            try:
                processor.getAnnotationsToManifest()
            except Exception as e:
                print(e)
    def getAnnotationsWithBody(self):
        for processor in self.queryProcessors:
            try:
                processor.getAnnotationsWithBody()
            except Exception as e:
                print(e)
    def getAnnotationsWithBodyAndTarget(self):
        for processor in self.queryProcessors:
            try:
                processor.getAnnotationsWithBodyAndTarget()
            except Exception as e:
                print(e)
    def getAnnotationsWithTarget(self):
        for processor in self.queryProcessors:
            try:
                processor.getAnnotationsWithTarget()
            except Exception as e:
                print(e)
    def getEntityById(self, entityId):#ciao Bruno, questo metodo non funziona perchè non è ancora finito.
                                        #In effetti, non capisco la sua descrizione nella documentazione.
                                        #Il metodo, in particolare, dovrebbe restituire oggetti della classe IdentifiableEntity()
                                        #In generale, perchè un oggetto della suddetta classe sia inizializzato, bisogna esclusivamente specificarne  l'id.
                                        #Se il metodo stesso prende in input un id, perchè non usare direttamente questo per creare l'oggetto della classe,
                                        #invece che passare obligatoriamente per una query del database, come specificato nella documentazione?
        result = []
        for processor in self.queryProcessors:
            try:
                result.append(processor.getEntityById(entityId))
            except Exception as e:
                print(e)
        return result


    def getCanvasesInCollection(self, collectionId):
        graph_db = DataFrame()
        relation_db = DataFrame()
        canvas_list = []
        for item in self.queryProcessors:
            if isinstance(item, TriplestoreQueryProcessor):
                graph_db = item.getCanvasesInCollection(collectionId)#restituisce canva, id, collection
            elif isinstance(item, RelationalQueryProcessor):
                relation_db = item.getEntities() #restituisce entityId, id, creator,title
        if not graph_db.empty:
            df_joined = merge(graph_db, relation_db, left_on="id", right_on="id")
            # itera le righe del dataframe e crea gli oggetti Canvas
            for index, row in df_joined.iterrows():
                canvas = Canvas(row['id'], row['label'], row['title'], row['creator'])
                canvas_list.append(canvas)
        return canvas_list 
    
    def getCanvasesInManifest(self, manifestId):
        graph_db = DataFrame()
        relation_db = DataFrame()
        canvas_list = []
        for item in self.queryProcessors:
            if isinstance(item, TriplestoreQueryProcessor):
                graph_db = item.getCanvasesInManifest(manifestId)
            elif isinstance(item, RelationalQueryProcessor):
                relation_db = item.getEntities() #restituisce entityId, id, title, creator
            else:
                break
        if not graph_db.empty:
            df_joined = merge(graph_db, relation_db, left_on="id", right_on="id")
            for index, row in df_joined.iterrows():
                    canvas = Canvas(row['id'], row['label'], row['title'], row['creator'])
                    canvas_list.append(canvas)
        return canvas_list 
    
    def getEntityById(self, id):#non ancora implementato
        for item in self.queryProcessors:
            if isinstance(item, TriplestoreQueryProcessor):
                graph_db = item.getEntitiesWithId(id)  
                for index, row in graph_db.iterrows(): 
                    entity = IdentifiableEntity(row['id'])
                    return entity
            else:
                pass
    def getEntitiesWithCreator(self, creator):
        graph_db = DataFrame()
        relation_db = DataFrame()
        for item in self.queryProcessors:  
            if isinstance(item, RelationalQueryProcessor):
                relation_db = item.getEntitiesWithCreator(creator) #restituisce entityId, id, title, creator
            else:
                pass
        if not relation_db.empty:
            id = [["id"]]
            for item in self.queryProcessors:  
                if isinstance(item, TriplestoreQueryProcessor):
                    for ind, item in id.iteritems:
                        graph_db = item.getEntitiesWithCreator(creator) #restituisce entityId, id, title, creator
                else:
                    pass
        entity_list =[]
        if not relation_db.empty:
            df_joined = merge(graph_db, relation_db, left_on="id", right_on="id")
            # itera le righe del dataframe e crea gli oggetti Canvas
            for index, row in df_joined.iterrows():
                entity = EntityWithMetadata(row['id'], row['label'], row['title'], row['creator'])
                entity_list.append(entity)
        return entity_list

# ERICA:

    def getEntitiesWithLabel(self, label):
        
        graph_db = DataFrame()
        relational_db = DataFrame()

        for processor in self.queryProcessors:
            if isinstance(processor, TriplestoreQueryProcessor):
                graph_db = processor.getEntitiesWithLabel(label)
            elif isinstance(processor, RelationalQueryProcessor):
                relational_db = processor.getEntities()
            else:
                break
            
        if not graph_db.empty: #check if the call got some result
            df_joined = merge(graph_db, relational_db, left_on="id", right_on="id") #create the merge with the two db
            df_joined_fill = df_joined.fillna("") 
            grouped = df_joined_fill.groupby("id").agg({
                                                        "label": "first",
                                                        "title": "first",
                                                        "creator": lambda x: "; ".join(x)
                                                    }).reset_index() #this is to avoid duplicates when we have more than one creator
            sorted = grouped.sort_values("id") #sorted for id

            if not sorted.empty: # if the merge has some result inside, proceed
        
                result = list()

                for row_idx, row in sorted.iterrows():
                    id = row["id"]
                    label = label
                    title = row["title"]
                    creators_row = row['creator']
                    for item in creators_row: # iterate the string and find out if there are some ";", if there are, split them
                        if item == ";":
                            creators = creators_row.split(';') # if it's a string the class attribute would automatically append every string in a list
                            break
                    else:
                        creators = [creators_row] # else, create a list and the class attribute will take it directly 

                    entities = EntityWithMetadata(id, label, title, creators)
                    result.append(entities)
                

                return result
            
            else: # if the merge got no result and is empty, then take only the result of the graph_db query and fill the attributes with empty strings
                result = list()

                for row_idx, row in graph_db.iterrows():
                    id = row["id"]
                    label = label
                    title = ""
                    creators = ""

                    entities = EntityWithMetadata(id, label, title, creators)
                    result.append(entities)
                

                return result
                

        
    def getEntitiesWithTitle(self, title):

        graph_db = DataFrame()
        relational_db = DataFrame()

        for processor in self.queryProcessors:
            if isinstance(processor, TriplestoreQueryProcessor):
                graph_db = processor.getAllEntities()
            elif isinstance(processor, RelationalQueryProcessor):
                relational_db = processor.getEntitiesWithTitle(title)
            else:
                break        
        

        if not graph_db.empty:
            df_joined = merge(graph_db, relational_db, left_on="id", right_on="id")

            result = list()

            for row_idx, row in df_joined.iterrows():
                id = row["id"]
                label = row["label"]
                title = title
                creators = row["creator"]
                entities = EntityWithMetadata(id, label, title, creators)
                result.append(entities)

        return result
        

    def getImagesAnnotatingCanvas(self, canvasId):

        graph_db = DataFrame()
        relational_db = DataFrame()

        for processor in self.queryProcessors:

            if isinstance(processor, TriplestoreQueryProcessor):
                graph_db = processor.getEntitiesWithCanvas(canvasId)
            elif isinstance(processor, RelationalQueryProcessor):
                relational_db = processor.getAllAnnotations()
            else:
                break

        if not graph_db.empty:
            df_joined = merge(graph_db, relational_db, left_on="id", right_on="target")
            result = list()

            for row_idx, row in df_joined.iterrows():
                id = row["body"]
                images = Image(id)
            result.append(images)

        return result
    

    def getManifestsInCollection(self, collectionId):

        graph_db = DataFrame()
        relational_db = DataFrame()
        
        for processor in self.queryProcessors:
            if isinstance(processor, TriplestoreQueryProcessor):
                graph_db = processor.getManifestsInCollection(collectionId)
            elif isinstance(processor, RelationalQueryProcessor):
                relational_db = processor.getEntities()
            else:
                break
        

        if not graph_db.empty:
            df_joined = merge(graph_db, relational_db, left_on="id", right_on="id") 

            if not df_joined.empty:
               
                result = list()

                for row_idx, row in df_joined.iterrows():
                    id = row["id"]
                    label = row["label"]
                    title = row["title"]
                    creators = row["creator"]
                    items = processor.getCanvasesInManifest(id)
                    manifests = Manifest(id, label, title, creators, items)
                    result.append(manifests)

            return result
        else: 
            result = list()

            for row_idx, row in graph_db.iterrows():
                id = row["id"]
                label = row["label"]
                title = ""
                creators = ""
                items = processor.getCanvasesInManifest(id)
                manifests = Manifest(id, label, title, creators, items)
                result.append(manifests)            

            return result


# NOTE: TEST BLOCK, TO BE DELETED
# TODO: DELETE COMMENTS
#  
# Uncomment for a test of query processor    
# qp = QueryProcessor()
# qp.setDbPathOrUrl(RDF_DB_URL)
# print(qp.getEntityById('https://dl.ficlit.unibo.it/iiif/2/28429/canvas/p1'))
# qp.setDbPathOrUrl(SQL_DB_URL)
# print(qp.getEntityById('https://dl.ficlit.unibo.it/iiif/2/28429/canvas/p1'))
# check library sparqldataframe




# grp_endpoint = "http://127.0.0.1:9999/blazegraph/sparql"
# qp = QueryProcessor()

# qp.setDbPathOrUrl(RDF_DB_URL)

# p = Processor()
# tqp = TriplestoreQueryProcessor()
# tqp.setDbPathOrUrl("http://127.0.0.1:9999/blazegraph/sparql")
# # print(qp.getEntityById('https://dl.ficlit.unibo.it/iiif/2/28429/canvas/p1'))

# generic = GenericQueryProcessor()
# generic.addQueryProcessor(qp)
# generic.addQueryProcessor(p)
# generic.addQueryProcessor(tqp)
#print(generic.getEntityById('https://dl.ficlit.unibo.it/iiif/2/28429/canvas/p1'))
#print(generic.getAllCanvases())

# col_dp = CollectionProcessor()
# col_dp.setDbPathOrUrl(grp_endpoint)
# col_dp.uploadData("data/collection-1.json")
# col_dp.uploadData("data/collection-2.json")

# # In the next passage, create the query processors for both
# # the databases, using the related classes
# rel_qp = RelationalQueryProcessor()
# rel_qp.setDbPathOrUrl(rel_path)

# grp_qp = TriplestoreQueryProcessor()
# grp_qp.setDbPathOrUrl(grp_endpoint)

# # Finally, create a generic query processor for asking
# # about data
# generic = GenericQueryProcessor()
# generic.addQueryProcessor(rel_qp)
# generic.addQueryProcessor(grp_qp)

# result_q1 = generic.getAllManifests()
# result_q3 = generic.getAnnotationsToCanvas("https://dl.ficlit.unibo.it/iiif/2/28429/canvas/p1")




# try1 = CollectionProcessor()
# try1.dbPathOrUrl = "http://192.168.1.55:9999/blazegraph/sparql"
# try1.getDbPathOrUrl()

# print(try1.uploadData("collection-1.json"))


# try2 = CollectionProcessor()
# try2.dbPathOrUrl = "http://192.168.1.55:9999/blazegraph/sparql"
# try2.getDbPathOrUrl()

# print(try2.uploadData("collection-2.json"))


# # create an instance of the TriplestoreQueryProcessor class
# query_processor = TriplestoreQueryProcessor()

# # call the getAllCanvases method to retrieve the canvases from the triplestore
# entity_df = query_processor.getEntitiesWithLabel('Raimondi, Giuseppe. Quaderno manoscritto, "Caserma Scalo : 1930-1968"')
# entity_dt = query_processor.getEntitiesWithLabel("Raimondi, Giuseppe. Quaderno manoscritto, \"Caserma Scalo : 1930-1968\"")
# # print the dataframe containing the canvases
# print(entity_df)
# print(entity_dt)




#upload_metadata= MetadataProcessor()
#upload_metadata.setDbPathOrUrl("database.db")
#upload_metadata.uploadData("metadata.csv")
#upload_annotation= AnnotationProcessor()
#upload_annotation.setDbPathOrUrl("database.db")
#upload_annotation.uploadData("annotations.csv")