from utils import read_conll

class ConlluGraph:
    def __init__(self):
        """ ConlluGraph. """

        pass

    def build_dataset(self, filename):
        """Reads an input CoNLL-U file and returns a list of ConlluToken objects for each token in a sentence."""

        print("Building dataset using {}".format(filename))
        annotated_sentences, comment_lines = read_conll(filename)      
        return annotated_sentences, comment_lines

    def build_edges(self, annotated_sentences):
        """Builds individual edges."""

        self.sentence_edges = []
        for annotated_sentence in annotated_sentences:
            # dictionary with conllu ID as key and a tuple of (id, head, rel) as value.
            self.edges = {}
            for token in annotated_sentence:
                self.edges[token.conllu_id] = []
                self.edges[token.conllu_id].append(self.create_edge(token))
            self.sentence_edges.append(self.edges)
        return self.sentence_edges

    def create_edge(self, current_token):
        """Creates a labelled edge between the current token and its head."""

        self.modifier = current_token.conllu_id
        self.head = current_token.head
        self.deprel = current_token.deprel
        return (self.modifier, self.head, self.deprel)

    def build_subgraph(self, token, sentence_graph, annotated_sentence):
        """ Builds subgraphs of child, parent and grandparent nodes. """
        
        parent_token = annotated_sentence[int(token.head)]
        grandparent_token = annotated_sentence[int(parent_token.head)]
        sub_graph = SubGraph(token, parent_token, grandparent_token)
        return sub_graph


class SubGraph(object):
    """ Creates a subgraph of 3 nodes. """
    def __init__(self, node1=None, node2=None, node3=None):
        self.node1 = node1
        self.node2 = node2
        self.node3 = node3

    def __str__(self):         
         return "{}|{} ({})  {}|{} ({})  {}|{}".format(self.node1.conllu_id, self.node1.lemma, self.node1.deprel,
                                                        self.node2.conllu_id, self.node2.word, self.node2.deps_set, 
                                                        self.node3.conllu_id, self.node3.word)






    
