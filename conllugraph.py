from utils import read_conll

class ConlluGraph:
    def __init__(self):
        """ ConlluGraph. """
        pass


    def build_dataset(self, filename):
        """Reads an input CoNLL-U file and returns ConlluToken objects for each token in a sentence."""

        print("Building dataset using {}".format(filename))
        graphs, annotated_sentences = read_conll(filename)
        
        return graphs, annotated_sentences


    def build_edges(self, annotated_sentences):
        """Builds a graph, e.g. a path from each token to its ancestors."""

        print("Building graphs from annotated sentences.")
        
        self.sentence_edges = []
        for annotated_sentence in annotated_sentences:
            # dictionary with conllu ID as key and a triple of (id, head, rel) as value.
            self.edges = {}
            for token in annotated_sentence:
                self.edges[token.id] = []
                self.edges[token.id].append(self.create_edge(token))
            
            self.sentence_edges.append(self.edges)

        return self.sentence_edges


    def create_edge(self, current_token):
        """Creates a labelled edge between the current token and its head."""

        self.modifier = current_token.id
        self.head = current_token.head
        self.deprel = current_token.deprel

        return (self.modifier, self.head, self.deprel)


    def evaluate_dataset(self, annotated_sentences):
        print("Evaluating dataset.")
        
        raise NotImplementedError
