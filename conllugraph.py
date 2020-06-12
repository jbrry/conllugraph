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


    def build_subgraph(self, token, sentence_graph, annotated_sentence):
        """ Builds subgraphs of child, parent and grandparent nodes.
        
        node1 (deprel) node2 (deprel) node3
        e.g. 3|at (case) 5|desk (nmod) 2|girl
        """

        # child / node 1
        part_1 = "{}|{} ({})".format(token.id, token.lemma, token.deprel)

        # check if the head is root
        if (int(token.head) - 1) == -1:
            raise ValueError
        # get `ConlluToken` of parent
        parent_token = annotated_sentence[int(token.head) - 1]
        parent_head = parent_token.head

        # parent / node 2
        part_2 = "{}|{} ({})".format(token.head, parent_token.word, parent_token.deprel)

        # get `ConlluToken` of grand-parent
        if (int(parent_head) - 1) == -1:
            grandparent = "*ROOT*"
        else:
            grandparent_token = annotated_sentence[int(parent_head) - 1]
            grandparent = grandparent_token.word
        
        # grandparent / node 3
        part_3 = "{}|{}".format(parent_head, grandparent)

        return "{} {} {}".format(part_1, part_2, part_3)

    def evaluate_dataset(self, annotated_sentences):
        print("Evaluating dataset.")
        
        raise NotImplementedError
