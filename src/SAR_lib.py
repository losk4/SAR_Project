import json
from nltk.stem.snowball import SnowballStemmer
import os
import re


class SAR_Project:
    """
    Prototipo de la clase para realizar la indexacion y la recuperacion de noticias
        
        Preparada para todas las ampliaciones:
          parentesis + multiples indices + posicionales + stemming + permuterm + ranking de resultado

    Se deben completar los metodos que se indica.
    Se pueden añadir nuevas variables y nuevos metodos
    Los metodos que se añadan se deberan documentar en el codigo y explicar en la memoria
    """

    # lista de campos, el booleano indica si se debe tokenizar el campo
    # NECESARIO PARA LA AMPLIACION MULTIFIELD
    fields = [("title", True), ("date", False),
              ("keywords", True), ("article", True),
              ("summary", True)]
    
    
    # numero maximo de documento a mostrar cuando self.show_all es False
    SHOW_MAX = 100


    def __init__(self):
        """
        Constructor de la classe SAR_Indexer.
        NECESARIO PARA LA VERSION MINIMA

        Incluye todas las variables necesaria para todas las ampliaciones.
        Puedes añadir más variables si las necesitas 

        """
        self.index = {} # hash para el indice invertido de terminos --> clave: termino, valor: posting list.
                        # Si se hace la implementacion multifield, se pude hacer un segundo nivel de hashing de tal forma que:
                        # self.index['title'] seria el indice invertido del campo 'title'.
        self.sindex = {} # hash para el indice invertido de stems --> clave: stem, valor: lista con los terminos que tienen ese stem
        self.ptindex = {} # hash para el indice permuterm.
        self.docs = {} # diccionario de documentos --> clave: entero(docid),  valor: ruta del fichero.
        self.weight = {} # hash de terminos para el pesado, ranking de resultados. puede no utilizarse
        self.news = {} # hash de noticias --> clave entero (newid), valor: la info necesaria para diferenciar la noticia dentro de su fichero (doc_id y posición dentro del documento)
        self.tokenizer = re.compile("\W+") # expresion regular para hacer la tokenizacion
        self.stemmer = SnowballStemmer('spanish') # stemmer en castellano
        self.show_all = False # valor por defecto, se cambia con self.set_showall()
        self.show_snippet = False # valor por defecto, se cambia con self.set_snippet()
        self.use_stemming = False # valor por defecto, se cambia con self.set_stemming()
        self.use_ranking = False  # valor por defecto, se cambia con self.set_ranking()

        #
        self.docID = 1
        self.newID = 1
        #


    ###############################
    ###                         ###
    ###      CONFIGURACION      ###
    ###                         ###
    ###############################


    def set_showall(self, v):
        """

        Cambia el modo de mostrar los resultados.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_all es True se mostraran todos los resultados el lugar de un maximo de self.SHOW_MAX, no aplicable a la opcion -C

        """
        self.show_all = v


    def set_snippet(self, v):
        """

        Cambia el modo de mostrar snippet.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_snippet es True se mostrara un snippet de cada noticia, no aplicable a la opcion -C

        """
        self.show_snippet = v


    def set_stemming(self, v):
        """

        Cambia el modo de stemming por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v


    def set_ranking(self, v):
        """

        Cambia el modo de ranking por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON RANKING DE NOTICIAS

        si self.use_ranking es True las consultas se mostraran ordenadas, no aplicable a la opcion -C

        """
        self.use_ranking = v




    ###############################
    ###                         ###
    ###   PARTE 1: INDEXACION   ###
    ###                         ###
    ###############################


    def index_dir(self, root, **args):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Recorre recursivamente el directorio "root" e indexa su contenido
        los argumentos adicionales "**args" solo son necesarios para las funcionalidades ampliadas

        """

        self.multifield = args['multifield']
        self.positional = args['positional']
        self.stemming = args['stem']
        self.permuterm = args['permuterm']

        for dir, subdirs, files in os.walk(root):
            for filename in files:
                if filename.endswith('.json'):
                    fullname = os.path.join(dir, filename)
                    self.index_file(fullname)


        

        ##########################################
        ## COMPLETAR PARA FUNCIONALIDADES EXTRA ##
        ##########################################

        if self.stemming:
            self.make_stemming()

        if self.permuterm:
            self.make_permuterm()

        #print(self.docs)
        #print(self.news)
        #print(self.index)
        #print(self.reverse_posting([5, 6, 10, 800, 801, 802]))
        #print(self.and_posting([5, 6, 10, 800, 801, 802], [6, 7, 8, 9, 10, 50, 100, 801]))
        #print(self.or_posting([5, 6, 10, 800, 801, 802], [6, 7, 8, 9, 10, 50, 100, 801]))
        #print(self.minus_posting([5, 6, 10, 800, 801, 802], [6, 7, 8, 9, 10, 50, 100, 801]))
        #print("---------")
        #print(self.and_posting([5, 6, 10, 800, 801, 802], [6, 7, 8, 9, 10, 50, 100, 801]))
        #print("---------")
        #print(self.reverse_posting(self.and_posting([5, 6, 10, 800, 801, 802], [6, 7, 8, 9, 10, 50, 100, 801])))
        #print("---------")
        #print(self.and_posting([5, 6, 10, 800, 801, 802], self.reverse_posting(self.and_posting([5, 6, 10, 800, 801, 802], [6, 7, 8, 9, 10, 50, 100, 801]))))
        

    def index_file(self, filename):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Indexa el contenido de un fichero.

        Para tokenizar la noticia se debe llamar a "self.tokenize"

        Dependiendo del valor de "self.multifield" y "self.positional" se debe ampliar el indexado.
        En estos casos, se recomienda crear nuevos metodos para hacer mas sencilla la implementacion

        input: "filename" es el nombre de un fichero en formato JSON Arrays (https://www.w3schools.com/js/js_json_arrays.asp).
                Una vez parseado con json.load tendremos una lista de diccionarios, cada diccionario se corresponde a una noticia

        """

        
        with open(filename) as fh:
            jlist = json.load(fh)

        #
        # "jlist" es una lista con tantos elementos como noticias hay en el fichero,
        # cada noticia es un diccionario con los campos:
        #      "title", "date", "keywords", "article", "summary"
        #
        # En la version basica solo se debe indexar el contenido "article"
        #
        #
        #
        #################
        ### COMPLETAR ###
        #################

        """
        Proceso de indexado:
        self.docs = {clave: docID, valor: filename}
        self.news = {clave: newID, valor: [docID, pos]}
        self.index = {clave: término, valor: [(newID)*] (la posting list básicamente)}
        Los ID's empiezan en 1 por defecto
        """
        pos = 1
        self.docs[self.docID] = filename

        for new in jlist:
            self.news[self.newID] = [self.docID, pos]
            pos += 1
            content = new["article"]
            tokens = set(self.tokenize(content))

            for token in tokens:
                if token not in self.index.keys():
                    self.index[token] = []
                self.index[token].append(self.newID)

            self.newID += 1
        self.docID += 1

        


    def tokenize(self, text):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Tokeniza la cadena "texto" eliminando simbolos no alfanumericos y dividientola por espacios.
        Puedes utilizar la expresion regular 'self.tokenizer'.

        params: 'text': texto a tokenizar

        return: lista de tokens

        """
        return self.tokenizer.sub(' ', text.lower()).split()



    def make_stemming(self):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING.

        Crea el indice de stemming (self.sindex) para los terminos de todos los indices.

        self.stemmer.stem(token) devuelve el stem del token

        """
        
        
        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################
        for token in self.index :
            stem = self.stemmer.stem(token)

            if(stem in self.sindex):
                # Alexey: no faltaría un "not"? O sea, relacionar el término con su correspondiente stem si todavía NO lo está.
                if(token not in self.sindex[stem]):
                    self.sindex[stem].append(token) 

            else:
                lista = [token]
                self.sindex[stem] = lista    


    
    def make_permuterm(self):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Crea el indice permuterm (self.ptindex) para los terminos de todos los indices.

        """
        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################
        """
        for token in self.index:
            lon = len(token)
            aux = 0
            primero = ''
            segundo= ''
            encontrado = False

            while aux < lon:
                if not encontrado:    
                    primero += token[aux]
                else:
                    segundo += token[aux]

                if token[aux] == '?' or token[aux] == '*':
                    encontrado = True
        """
        for token in self.index:
            lon = len(token)
            aux = 0
            
            perm = token + '*'

            if perm in self.ptindex:
                if token not in self.ptindex[perm]:
                    self.ptindex[perm].append(token)
            else:
                lista = [token]
                self.ptindex[perm] = lista 

            while aux < lon: 
                perm =  perm[1:] + perm[0]

                if perm in self.ptindex:
                    if token not in self.ptindex[perm]:
                        self.ptindex[perm].append(token)
                else:
                    lista = [token]
                    self.ptindex[perm] = lista 

                aux+=1
                

    def show_stats(self):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Muestra estadisticas de los indices
        
        """
        pass
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        print("========================================")
        print("Number of indexed days: " )
        print("----------------------------------------")
        print("Number of indexed news: " + str(len(self.news)))
        print("----------------------------------------")
        print("TOKENS:")
        print("\t # of tokens in 'article': " + str(len(self.index)))
        print("----------------------------------------")

        if self.permuterm:
            print("PERMUTERMS:")
            ##print(self.ptindex)
            print("\t # of permuters in 'article': " + str(len(self.ptindex)))

        print("----------------------------------------")

        if self.stemming:
            print("STEMS:")
            ##self.make_stemming()
            ##print(self.sindex)
            print("\t # of stems in 'article': " + str(len(self.sindex)))
        print("========================================")
        

    ###################################
    ###                             ###
    ###   PARTE 2.1: RECUPERACION   ###
    ###                             ###
    ###################################


    def solve_query(self, query, prev={}):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una query.
        Debe realizar el parsing de consulta que sera mas o menos complicado en funcion de la ampliacion que se implementen


        param:  "query": cadena con la query
                "prev": incluido por si se quiere hacer una version recursiva. No es necesario utilizarlo.


        return: posting list con el resultado de la query

        """
        
        if query is None or len(query) == 0:
            return []

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        """
        querylist= query.split()
        lon = len(querylist)
        aux = 0
        res = []

        while aux < lon:
            if querylist[aux] == 'NOT':
                res = self.reverse_posting(self.get_posting(querylist[aux+1]))
                if aux + 2 == lon:
                    return res
                aux += 2 

            elif aux + 1 == lon:
                res = self.get_posting(querylist[aux])
                return res
                           
            else:
                if querylist[aux] == 'AND':
                    if querylist[aux+1] == 'NOT':
                        no = self.reverse_posting(self.get_posting(querylist[aux+2]))
                        res = self.and_posting(res, no)
                        aux += 3
                    else:
                        res = self.and_posting(res, self.get_posting(querylist[aux+1]))
                        aux += 2
                if querylist[aux] == 'OR':
                    if querylist[aux+1] == 'NOT':
                        no = self.reverse_posting(self.get_posting(querylist[aux+2]))
                        res = self.or_posting(res, no)
                        aux += 3
                    else:
                        res = self.or_posting(res, self.get_posting(querylist[aux+1]))
                        aux += 2
                if querylist[aux] != 'OR' and querylist[aux] != 'AND':
                    res = self.get_posting(querylist[aux])
                    aux += 1
                    
        return res
        """
        qTokens = query.split()
        qList = []
        qTuple = []
        qAnswer = []

        for token in qTokens:
            if token == 'NOT' or token == 'AND' or token == 'OR':
                qTuple.append(token)
            else:
                qTuple.append(token)
                qList.append(qTuple)
                qTuple = []

        temp = []
        for tuple in qList:
            tupleLength = len(tuple)
            i = tupleLength - 2
            temp = self.get_posting(tuple[tupleLength - 1])

            if(tupleLength == 1):
                qAnswer = temp
            else:
                while i >= 0:
                    if tuple[i] == 'NOT':
                        temp = self.reverse_posting(temp)
                        if(tupleLength == 2):
                            qAnswer = temp
                    elif tuple[i] == 'AND':
                        qAnswer = self.and_posting(qAnswer, temp)
                    elif tuple[i] == 'OR':
                        qAnswer = self.or_posting(qAnswer, temp)       
                    i -= 1

        return qAnswer


    def get_posting(self, term, field='article'):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve la posting list asociada a un termino. 
        Dependiendo de las ampliaciones implementadas "get_posting" puede llamar a:
            - self.get_positionals: para la ampliacion de posicionales
            - self.get_permuterm: para la ampliacion de permuterms
            - self.get_stemming: para la amplaicion de stemming


        param:  "term": termino del que se debe recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        result = []

        if('*' in term) or ('?' in term):
                result = self.get_permuterm(term)

        elif(self.use_stemming):
            if term in self.index:
                result = self.get_stemming(term)

        else:
            if(term in self.index):
                result = self.index[term]

        return result


    def get_positionals(self, terms, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE POSICIONALES

        Devuelve la posting list asociada a una secuencia de terminos consecutivos.

        param:  "terms": lista con los terminos consecutivos para recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        pass
        ########################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE POSICIONALES ##
        ########################################################


    def get_stemming(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE STEMMING

        Devuelve la posting list asociada al stem de un termino.

        param:  "term": termino para recuperar la posting list de su stem.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        
        stem = self.stemmer.stem(term)

        if stem in self.sindex.keys():           
            lista = self.sindex[stem]
        else:
            return []

        lon = len(lista)
        res = []
        aux = 0
        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################
        while aux < lon:
            res = self.or_posting(res,self.index[lista[aux]])
            aux += 1
        return res


    def get_permuterm(self, term, field='article'):
        """
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        Devuelve la posting list asociada a un termino utilizando el indice permuterm.

        param:  "term": termino para recuperar la posting list, "term" incluye un comodin (* o ?).
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """

        ##################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA PERMUTERM ##
        ##################################################
        perm = []

        if ('*' not in term) and ('?' not in term):
            perm = term + '$'
            print('1')
        else:
            if '*' in term:
                varias = True
                posicion = term.index('*')
                print('2')

            if '?' in term:
                varias = False
                posicion = term.index('?')    
                print('3')
            """
            if posicion == 0:
                # term + '$' 
                print('4')
                patron = term[1:] +'*.' 
                print(patron)
                for clave in self.ptindex:
                    if re.search(patron, clave):
                        perm = clave

            elif posicion == len(term) - 1 :
                #  '$' + term 
                print('5')
                patron = '*' + term[0:posicion-1] + '.' 
                for clave in self.ptindex:
                    if re.search(patron, clave):
                        perm = clave
            else: 
                """
            if varias: 
                patron = term[posicion+1:] + '*' + term[0:posicion]
                for clave in self.ptindex.keys():
                    if len(patron) <= len(clave) - 1:
                        encontrado = True
                        lon_p = len(patron)
                        aux2 = 0
                        while (aux2 < lon_p) and (aux2 < len(clave)):
                            if patron[aux2] != clave[aux2]:
                                encontrado = False
                            aux2 += 1
                    
                        if encontrado:
                            perm.append(clave) 

            else:
                patron = term[posicion+1:] + '*' + term[0:posicion]
                for clave in self.ptindex.keys():
                    if len(patron) == len(clave) - 1:
                        encontrado = True
                        lon_p = len(patron)
                        aux2 = 0
                        while (aux2 < lon_p) and (aux2 < len(clave)):
                            if patron[aux2] != clave[aux2]:
                                encontrado = False
                            aux2 += 1
                    
                        if encontrado:
                            perm.append(clave) 

        lista =[]

        for p in perm:
            if p in self.ptindex.keys():           
                lista += self.ptindex[p]
            else:
                return []

        lon = len(lista)
        res = []
        aux = 0
        
        while aux < lon:
            res = self.or_posting(res,self.index[lista[aux]])
            aux += 1
        return res



    def reverse_posting(self, p):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve una posting list con todas las noticias excepto las contenidas en p.
        Util para resolver las queries con NOT.


        param:  "p": posting list


        return: posting list con todos los newid exceptos los contenidos en p

        """

        #res = []
        #for newID in self.news.keys():
        #    if newID not in p:
        #        res += [newID]
        #
        #return res

        res = []
        pID = 0
        for newID in self.news.keys():
            if pID == len(p):
                res += [newID]
            elif not(newID >= p[pID]):
                res += [newID]
            else:
                pID += 1

        return res

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def and_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el AND de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos en p1 y p2

        """
        
        #res = []
        #for newID2 in p2:
        #    if newID2 in p1:
        #        res += [newID2]
        #
        #return res
        
        res = []
        p1ID = 0
        p2ID = 0
        while p1ID < len(p1) and p2ID < len(p2):
            if p1[p1ID] == p2[p2ID]:
                res += [p1[p1ID]]
                p1ID += 1
                p2ID += 1
            elif p1[p1ID] < p2[p2ID]:
                p1ID += 1
            else:
                p2ID += 1

        return res

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def or_posting(self, p1, p2):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el OR de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 o p2

        """

        res = []
        p1ID = 0
        p2ID = 0
        while p1ID < len(p1) and p2ID < len(p2):
            if p1[p1ID] == p2[p2ID]:
                res += [p1[p1ID]]
                p1ID += 1
                p2ID += 1
            elif p1[p1ID] < p2[p2ID]:
                res += [p1[p1ID]]
                p1ID += 1
            else:
                res += [p2[p2ID]]
                p2ID += 1
        
        while p1ID < len(p1):
            res += [p1[p1ID]]
            p1ID += 1
        while p2ID < len(p2):
            res += [p2[p2ID]]
            p2ID += 1
        
        return res

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################


    def minus_posting(self, p1, p2):
        """
        OPCIONAL PARA TODAS LAS VERSIONES

        Calcula el except de dos posting list de forma EFICIENTE.
        Esta funcion se propone por si os es util, no es necesario utilizarla.

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los newid incluidos de p1 y no en p2

        """
        #[5, 6, 10, 800, 801, 802], [6, 7, 8, 9, 10, 50, 100, 801]

        res = []
        p1ID = 0
        p2ID = 0
        while p1ID < len(p1) and p2ID < len(p2):
            if p1[p1ID] == p2[p2ID]:
                p1ID += 1
                p2ID += 2
            elif p1[p1ID] < p2[p2ID]:
                res += [p1[p1ID]]
                p1ID += 1
            else:
                p2ID += 1
        
        while p1ID < len(p1):
            res += [p1[p1ID]]
            p1ID += 1
        
        return res
        ########################################################
        ## COMPLETAR PARA TODAS LAS VERSIONES SI ES NECESARIO ##
        ########################################################





    #####################################
    ###                               ###
    ### PARTE 2.2: MOSTRAR RESULTADOS ###
    ###                               ###
    #####################################


    def solve_and_count(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra junto al numero de resultados 

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T

        """
        result = self.solve_query(query)
        print("%s\t%d" % (query, len(result)))
        return len(result)  # para verificar los resultados (op: -T)


    def solve_and_show(self, query):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra informacion de las noticias recuperadas.
        Consideraciones:

        - En funcion del valor de "self.show_snippet" se mostrara una informacion u otra.
        - Si se implementa la opcion de ranking y en funcion del valor de self.use_ranking debera llamar a self.rank_result

        param:  "query": query que se debe resolver.

        return: el numero de noticias recuperadas, para la opcion -T
        
        """
        result = self.solve_query(query)
        if self.use_ranking:
            result = self.rank_result(result, query)   

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        n = 0
        print("========================================")
        print("Query: '" + query + "'")
        print("Number of results: " + str(len(result)))
        print("------------------------")

        # Simplificar usando regex!
        if self.show_snippet:
            terms = []
            qList = query.split()
            for token in qList:
                if token != "NOT" and token != "AND" and token != "OR":
                    terms.append(token)

        for newID in result:
            filename = self.docs[self.news[newID][0]]
            position = self.news[newID][1]

            if not self.show_all and n > self.SHOW_MAX - 1:
                break

            with open(filename) as fh:
                jlist = json.load(fh)
                date = jlist[position - 1]["date"]
                title = jlist[position - 1]["title"]
                keywords = jlist[position - 1]["keywords"]
                score = 0
                n += 1

                if self.show_snippet:
                    content = jlist[position - 1]["article"]
                    snippet = None
                    print("#" + str(n))
                    print("Score: " + str(score))
                    print(str(newID))
                    print("Date: " + date)
                    print("Title: " + title)
                    print("Keywords: " + keywords)

                    for term in terms:
                        tokens = self.tokenize(content)
                        try:
                            index = tokens.index(term)
                            if index - 5 >= 0:
                                print("..." + ' '.join(tokens[index - 5:index + 5]) + "...")
                            else:
                                print("..." + ' '.join(tokens[index:index + 10]) + "...")
                        except ValueError:
                                print("...TERM (" + term + ") NOT IN ARTICLE CONTENT...")

                    print("------------------------")
                else:
                    print("#"+str(n)+"\t"+"("+str(score)+") ("+str(newID)+") ("+date+") "+title+"\t("+keywords+")")
                    
        return len(result)


    def rank_result(self, result, query):
        """
        NECESARIO PARA LA AMPLIACION DE RANKING

        Ordena los resultados de una query.

        param:  "result": lista de resultados sin ordenar
                "query": query, puede ser la query original, la query procesada o una lista de terminos


        return: la lista de resultados ordenada

        """

        pass
        
        ###################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE RANKING ##
        ###################################################
