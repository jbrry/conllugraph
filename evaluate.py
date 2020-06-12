from collections import Counter

class EvaluateConllu(object):
    def __init__(self):
        """ EvaluateConllu. """
        pass


    def evaluate(self, sentence_graphs, annotated_sentences):
        """ """

        for sentence_graph, annotated_sentence in zip(sentence_graphs, annotated_sentences):

            print(sentence_graph)
            print(annotated_sentence)
            self.evaluate_labels(sentence_graph, annotated_sentence)


    def evaluate_labels(self, sentence_graph, annotated_sentence):
        """ Evaluates certain dependency labels, e.g. case, mark """

        deprel_count = Counter()
        
        for token_id, edge in sentence_graph.items():
            # get `ConlluToken`
            token = annotated_sentence[int(token_id) - 1]

            edge = edge.pop()
            # (m, h, r)
            deprel = str(edge[-1])

            if deprel == "case":
                deprel_count.update([deprel])

                # build triple edge
                triple = self.extract_subgraphs(token)

                # TODO

            elif deprel == "mark":
                pass

            
        print(case_count)

    def extract_subgraphs(token):
        """Extractions grandchild, parent and grandparent information."""
        pass




















