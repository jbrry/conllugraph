from collections import Counter
from conllugraph import ConlluGraph
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluateConllu(object):
    def __init__(self, evaluate_edges, evaluate_labels, attach_morphological_case, visualise):
        """ EvaluateConllu. """
        
        # edges
        self.edge_count = 0
        self.dummy_root_count = 0

        # deprels
        self.deprel_count = Counter()
        self.modifier_lemmas = Counter()
        self.morph_case = Counter()

        # Boolean flags
        self.evaluate_edges = evaluate_edges
        self.evaluate_labels = evaluate_labels
        self.attach_morphological_case = attach_morphological_case
        self.visualise = visualise


    def evaluate(self, sentence_graphs, annotated_sentences):
        """ Perform various types of evaluation. """

        for sentence_graph, annotated_sentence in zip(sentence_graphs, annotated_sentences):

            # evaluate heads/arcs
            if self.evaluate_edges:
                self.edge_count, self.dummy_root_count = self.evaluate_heads(sentence_graph, annotated_sentence)


            # evaluate certain labels
            if self.evaluate_labels:
                self.deprel_count, self.modifier_lemmas, self.morph_case = self.evaluate_deprels(sentence_graph, annotated_sentence)



        return self.edge_count, self.dummy_root_count, self.deprel_count, self.modifier_lemmas, self.morph_case


    def evaluate_heads(self, sentence_graph, annotated_sentence):
        """ """
        for token_id, edge in sentence_graph.items():
            token = annotated_sentence[int(token_id)]
            
            # skip ROOT
            if token.head != -1:
                deps = token.deps_set
                num_deps = len(deps)
                # only consider extra dummy root edges (assumes the parser only chose one edge when choosing the real root)
                if num_deps > 1:
                    for dep in deps:
                        if dep == ('0', 'root'):
                            self.dummy_root_count += 1

                self.edge_count += num_deps
        
        return self.edge_count, self.dummy_root_count




    def evaluate_deprels(self, sentence_graph, annotated_sentence):
        """ Evaluates certain dependency labels, e.g. case, mark etc. """
        
        for token_id, edge in sentence_graph.items():
            token = annotated_sentence[int(token_id)]
            edge = edge.pop()
            # (m, h, r)
            deprel = str(edge[-1])

            if deprel == "case":
                self.deprel_count, self.modifier_lemmas, self.morph_case = self.evaluate_case(token, sentence_graph, annotated_sentence, deprel)

        return self.deprel_count, self.modifier_lemmas, self.morph_case 


    def evaluate_case(self, token, sentence_graph, annotated_sentence, deprel):
        """ Evaluates case labels to see if the grandchild lemma is 
        attached in the enhanced deprel of its parent. """

        LEMMAS_TO_IGNORE = ["'s", "-","@"]

        conllu_graph = ConlluGraph()
        self.deprel_count.update([deprel])
        # get child, parent, grandparent subgraph
        sub_graph = conllu_graph.build_subgraph(token, sentence_graph, annotated_sentence)
        modifier_lemma = token.lemma
        # check if the lemma has fixed children
        for child in token.children:
            if child.deprel == "fixed":
                # attach fixed children to lemma form
                modifier_lemma = modifier_lemma + "_" + child.lemma

        # make a copy of the lemma
        modifier_lemma_copy = modifier_lemma

        parent_deps = sub_graph.node2.deps_set

        # Check case from morph feats
        if self.attach_morphological_case:
            parent_morph_feats = sub_graph.node2.feats_set
            # some tokens won't have this key
            try:
                parent_morph_case = parent_morph_feats["Case"]
                self.morph_case.update([parent_morph_case])
                parent_morph_string = ":" + parent_morph_case
            except:
                KeyError
                parent_morph_string = ""


        self.attached_lemma = False
        # check each of the deps items
        for dep_item in parent_deps:
            if not self.attached_lemma:
                e_deprel = dep_item[1]
                parts = e_deprel.split(":")
                label_suffix = parts[-1]

                if self.attach_morphological_case:
                    # e_deprel and the morph case
                    label_suffix = parts[-2:]
                    label_suffix = ":".join(label_suffix)
                    modifier_lemma = modifier_lemma_copy + parent_morph_string

                if modifier_lemma.lower() == label_suffix:
                    self.modifier_lemmas.update(["case_attached"])
                    self.attached_lemma = True

                    if self.visualise:
                        print(str(sub_graph))
                        print(f"{clr.PASS}right lemma: {modifier_lemma} ===> {label_suffix} {clr.ENDC}")

        if not self.attached_lemma:
            # cases where we shouldn't be attaching a lemma
            if label_suffix == "root":
                self.modifier_lemmas.update(["ignored root"])
            elif label_suffix == "poss":
                self.modifier_lemmas.update(["ignored poss"])
            elif label_suffix == "parataxis":
                self.modifier_lemmas.update(["ignored parataxis"])
            elif label_suffix == "ref":
                self.modifier_lemmas.update(["ignored ref"])
            elif modifier_lemma in LEMMAS_TO_IGNORE:
                self.modifier_lemmas.update(["ignored non-string lemma"])
            else:
                self.modifier_lemmas.update(["case missed"])
                
                if self.visualise:
                    print(str(sub_graph))
                    print(f"{clr.FAIL}wrong lemma: {modifier_lemma} ===> {label_suffix}{clr.ENDC}")

        return self.deprel_count, self.modifier_lemmas, self.morph_case 


    def evaluate_mark(self, token, sentence_graph, annotated_sentence, deprel):
        """ Evaluates mark labels to see if the grandchild lemma is 
        attached in the enhanced deprel of its parent. """


        return self.deprel_count, self.modifier_lemmas


class clr:
    """
    Prints coloured text in terminal.
    https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-terminal-in-python
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    PASS = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
