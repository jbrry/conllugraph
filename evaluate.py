from collections import Counter
from conllugraph import ConlluGraph

class EvaluateConllu(object):
    def __init__(self):
        """ EvaluateConllu. """
        
        self.deprel_count = Counter()


    def evaluate(self, sentence_graphs, annotated_sentences):
        """ Perform various types of evaluation. """

        for sentence_graph, annotated_sentence in zip(sentence_graphs, annotated_sentences):
            self.evaluate_labels(sentence_graph, annotated_sentence)


    def evaluate_labels(self, sentence_graph, annotated_sentence):
        """ Evaluates certain dependency labels, e.g. case, mark """

        conllu_graph = ConlluGraph()
        
        for token_id, edge in sentence_graph.items():
            # get `ConlluToken`
            token = annotated_sentence[int(token_id) - 1]
            edge = edge.pop()
            # (m, h, r)
            deprel = str(edge[-1])
            
            if deprel == "acl":
                self.deprel_count.update([deprel])
                subgraph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
                print(subgraph)

            elif deprel == "case":
                self.deprel_count.update([deprel])
                subgraph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
                print(subgraph)

            elif deprel == "conj":
                self.deprel_count.update([deprel])
                subgraph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
                print(subgraph)

            elif deprel == "mark":
                self.deprel_count.update([deprel])
                subgraph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
                print(subgraph)
            
            elif deprel == "nmod":
                self.deprel_count.update([deprel])
                subgraph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
                print(subgraph)


            elif deprel == "obl":
                self.deprel_count.update([deprel])
                subgraph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
                print(subgraph)

            # RelClause 
            elif deprel == "acl:relcl":
                self.deprel_count.update([deprel])
                subgraph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
                print(subgraph)

            # acl: advcl: ?

            
        #print(self.deprel_count)



















