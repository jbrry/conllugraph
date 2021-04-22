import sys
import os.path
from collections import Counter

from conllugraph import ConlluGraph


LONG_BASIC_LABELS = ["nmod:poss", "nsubj:pass", "nsubj:xsubj", "acl:relcl", "aux:pass", "compound:prt", "obl:npmod", "det:predet", "nmod:npmod", "cc:preconj"] # Add any more or get this from a Vocab file

LABELS_TO_EXCLUDE = ["root", "poss", "parataxis", "ref"]


def write_output_file(input_path, delexicalised_sentences):
    """
    Takes an input path and the delexicalsed sentences and writes them to an output
    file in CoNLL-U format.
    """

    dirname = os.path.dirname(input_path)
    basename = os.path.basename(input_path)

    parent_dirs = dirname.split("/")
    train_dev_path = parent_dirs[-2]
    train_dev_path = train_dev_path + "-delexicalised"
    parent_dirs[-2] = train_dev_path
    output_path = parent_dirs
    output_path = "/".join(output_path)

    if not os.path.exists(output_path):
        print(f"Creating output path {output_path}")
        os.makedirs(output_path)

    outfile = os.path.join(output_path, basename)
    with open(outfile, 'w', encoding='utf-8') as fo:
        for sent in delexicalised_sentences:
            for conllu_token in sent[1:]: # skip ROOT
                fo.write(str(conllu_token) + "\n")
            fo.write("\n")


class DelexicaliseConllu(object):
    def __init__(self,
                attach_morphological_case,
                visualise
                ):
        """
        DelexicaliseConllu
        
        Params:
            attach_morphological_case: whether to attach the "Case" attribute from the morphological features.
            visualise: print outputs
        """
        self.attach_morphological_case = attach_morphological_case
        self.visualise = visualise
        
        # Counters
        self.deprel_count = Counter()
        self.lexical_item_count = Counter()
        self.lexicalised_deprels_count = Counter()


    def delexicalise(self, sentence_graphs, annotated_sentences):
        """Perform various types of delexicalisation."""

        output_delexicalised_sentences = []

        for sentence_graph, annotated_sentence in zip(sentence_graphs, annotated_sentences):
            # Delexicalise enhanced relations which involve 'case' and 'mark' dependents.
            delexicalised_case_mark_cc, deprel_count, lexical_item_count, \
                lexicalised_deprels_count = self.delexicalise_case_mark_cc(sentence_graph, annotated_sentence)
            output_delexicalised_sentences.append(delexicalised_case_mark_cc)
        
        return output_delexicalised_sentences, deprel_count, lexical_item_count, lexicalised_deprels_count

    def delexicalise_case_mark_cc(self, sentence_graph, annotated_sentence):
        """
        This delexicalisation procedure involves, for each word,
        checking its dependency label; if it contains lexical information,
        search for its dependents, if the token has a 'case', 'mark' or 'cc' dependent,
        the enhanced label will be set to a placeholder label which
        will be reconstructed in a post-processing step.
        """

        delexicalised_sentence = []

        for token_id, edge in sentence_graph.items():
            # Operate on each token
            token = annotated_sentence[int(token_id)]
            
            edeps = token.deps.split("|")
            for i, edep in enumerate(edeps):
                enhanced_label = edep.split(":")[1:]
                enhanced_label_string = ":".join(enhanced_label)

                # Likely a lexicalised head
                if len(enhanced_label) >= 2:
                    if enhanced_label_string not in LONG_BASIC_LABELS:
                        self.lexicalised_deprels_count.update([f"{enhanced_label_string}"])

                        # Look at the token's children and see if they have modifiers which involve attaching a lemma.
                        for token_child in token.children:
                            token_child_edeps = token_child.deps.split("|")
                            for token_child_edep in token_child_edeps:
                                token_child_enhanced_label = token_child_edep.split(":")[1:].pop()

                                # 1) Token has a "case" dependent
                                if token_child_enhanced_label == "case":
                                    lexical_item = edep.split(":")[-1]
                                    edep = edep.replace(lexical_item, "<case_delex>")
                                    edeps[i] = edep
                                    # update counters
                                    self.deprel_count.update(["case delexicalised"])
                                    self.lexical_item_count.update([lexical_item])

                                # 2) Token has a "mark" dependent
                                elif token_child_enhanced_label == "mark":
                                    lexical_item = edep.split(":")[-1]
                                    edep = edep.replace(lexical_item, "<mark_delex>")
                                    edeps[i] = edep
                                    # update counters
                                    self.deprel_count.update(["mark delexicalised"])
                                    self.lexical_item_count.update([lexical_item])

                                # 3) Token has a "cc" dependent
                                elif token_child_enhanced_label == "cc":
                                    lexical_item = edep.split(":")[-1]
                                    edep = edep.replace(lexical_item, "<cc_delex>")
                                    edeps[i] = edep
                                    # update counters
                                    self.deprel_count.update(["cc delexicalised"])
                                    self.lexical_item_count.update([lexical_item])

            # update token deps
            token.deps= "|".join(edeps)
            delexicalised_sentence.append(token)

        return delexicalised_sentence, self.deprel_count, self.lexical_item_count, self.lexicalised_deprels_count
                                
    def delexicalise_conj():
        """
        This delexicalisation procedure involves, for each word,
        checking its dependency label; if it contains lexical information,
        search for its dependents, if the token has a 'case' or 'mark' dependent,
        the enhanced label will be set to a placeholder label which
        will be reconstructed in a post-processing step.

        See "# text = Itinerary Both ships go to Caribbean Islands like Jamaica, Grand Cayman, Cozumel, St. Thomas, the Bahamas and St. Martin / St. Maarten."
        -> all tokens in a chain of conjs take the same label, and also attach the same cc label.
        """
        # 3) Token "conj" label, so delexicalise its "cc" dependents
        # 3b) The word the token is in conjunction with, it usually takes its edep label too (5:advcl:on|9:conj:and)
            # 10      to      to      PART    TO      _       11      mark    11:mark _
            # 11      go      go      VERB    VB      VerbForm=Inf    6       advcl   6:advcl:to      _
            # 12      ahead   ahead   ADV     RB      _       11      advmod  11:advmod       _
            # 13      and     and     CCONJ   CC      _       14      cc      14:cc   _
            # 14      replace replace VERB    VB      VerbForm=Inf    11      conj    6:advcl:to|11:conj:and  _

        base_relation = enhanced_label[0]
        if base_relation == "conj":
            print("\n")
            print(annotated_sentence)
            print(edeps)
            first_conjunct = edep.split(":")[0]
            print(first_conjunct)
            first_conjunct_token = annotated_sentence[int(first_conjunct)]
            first_conjunct_token_eheads = first_conjunct_token.deps

            lexical_item = edep.split(":")[-1]
            print(first_conjunct_token_eheads)
            
            # What is the word it is pointing to's head?
            # e.g. copy the conjunct's head
            # go to token 11, take its label....
            for token_child in token.children:
                token_child_edeps = token_child.deps.split("|")
                for token_child_edep in token_child_edeps:
                    token_child_edep_label = token_child_edep.split(":")[1:].pop()

                    if token_child_edep_label == "cc":
                        lexical_item = edep.split(":")[-1]
                        edep = edep.replace(lexical_item, "<cc_delex>")
                        print("cc dep", lexical_item, edeps, edep) # cc   <mark_delex> ['15:advcl:as', '19:conj:and'] 19:conj:<cc_delex> ???


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('-i', '--input', type=str,
    help='Input CoNLL-U file.')
    ap.add_argument('-e', '--encoding', default='utf-8', type=str,
    help='Type of encoding.')
    ap.add_argument('-mc', '--attach_morphological_case', default=False, action='store_true',
    help='Whether to append morphological case to enhanced label.')
    ap.add_argument('-v', '--visualise', default=False, action='store_true',
    help='Whether to visualise the dependency labels.')
    ap.add_argument('-ws', '--write-stats', metavar='FILE', default=None,
    help='Write statistics.')
    ap.add_argument('-q', '--quiet', default=False, action='store_true',
    help='Do not display certain helper information.')
    return ap

def main(argv):
    args = argparser().parse_args(argv[1:])

    conllu_graph = ConlluGraph()

    if args.input:
        base_input = os.path.basename(args.input)
        input_annotated_sentences = conllu_graph.build_dataset(args.input)
        input_sentence_edges = conllu_graph.build_edges(input_annotated_sentences)

        delexicalise_conllu = DelexicaliseConllu(args.attach_morphological_case, args.visualise)
        output_delexicalised_sentences, deprel_count, lexical_item_count, lexicalised_deprels_count = delexicalise_conllu.delexicalise(input_sentence_edges, input_annotated_sentences)

        conllu_out = write_output_file(args.input, output_delexicalised_sentences)

        # print(deprel_count)
        # print(lexical_item_count)
        # print(lexicalised_deprels_count)
        # print(output_delexicalised_sentences)
    
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))