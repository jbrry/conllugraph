from collections import Counter
from conllugraph import ConlluGraph
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluateConllu(object):
    def __init__(self):
        """ EvaluateConllu. """
        
        self.deprel_count = Counter()
        self.modifier_lemmas = Counter()
        

    def evaluate(self, sentence_graphs, annotated_sentences):
        """ Perform various types of evaluation. """

        for sentence_graph, annotated_sentence in zip(sentence_graphs, annotated_sentences):
            self.evaluate_labels(sentence_graph, annotated_sentence)


    def evaluate_labels(self, sentence_graph, annotated_sentence):
        """ Evaluates certain dependency labels, e.g. case, mark etc."""

        conllu_graph = ConlluGraph()
        for token_id, edge in sentence_graph.items():
            token = annotated_sentence[int(token_id)]
            edge = edge.pop()
            # (m, h, r)
            deprel = str(edge[-1])

            if deprel == "case":
                self.deprel_count.update([deprel])
                sub_graph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
                modifier_lemma = sub_graph.node1.lemma
                parent_deps = sub_graph.node2.deps_set

                for dep_item in parent_deps:
                    e_deprel = dep_item[1]
                    parts = e_deprel.split(":")
                    label_suffix = parts[-1]
                    if modifier_lemma == label_suffix:
                        self.modifier_lemmas.update(["case_attached"])
                    else:
                        self.modifier_lemmas.update(["case_missed"])
                        # adjust for cases of mwts/poss?
                        print(f"wrong lemma: {modifier_lemma} ===> {label_suffix}")

        return self.deprel_count, self.modifier_lemmas


















