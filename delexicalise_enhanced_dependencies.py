import sys
import os.path
from collections import Counter

from conllugraph import ConlluGraph


LONG_BASIC_LABELS = ["nmod:poss", "nsubj:pass", "nsubj:xsubj", "acl:relcl", "aux:pass", "compound:prt", "obl:npmod", "det:predet", "nmod:npmod", "cc:preconj"] # Add any more or get this from a Vocab file

LABELS_TO_EXCLUDE = ["root", "poss", "parataxis", "ref"]

"""
Bugged sentences:
Because the US and Pakistan have managed to capture or kill about 2/3s of the top 25 al-Qaeda commanders, the middle managers are not in close contact with al-Zawahiri and Bin Laden.
"""


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
            for conllu_token in sent:
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


    def delexicalise(self, annotated_sentences):
        """Perform various types of delexicalisation."""

        output_delexicalised_sentences = []

        for annotated_sentence in annotated_sentences:
            # Delexicalise enhanced relations which involve 'case' and 'mark' dependents.
            delexicalised_case_mark_cc, deprel_count, lexical_item_count, \
                lexicalised_deprels_count = self.delexicalise_case_mark_cc(annotated_sentence)

            # We have delexicalised the labels where tokens have certain modifiers,
            # but we still need to make sure these are applied to conjs which do not have direct
            # modifiers, so they have to get their delexicalised label from the first conjunct.
            delexicalised_conjs = self.propagate_first_conj_labels(delexicalised_case_mark_cc)
            # Now propagate 'cc' modifier to all conjuncts
            delexicalised_conjs = self.propagate_cc_modifier_in_conjs(delexicalised_conjs)

            output_delexicalised_sentences.append(delexicalised_conjs)
        
        return output_delexicalised_sentences, deprel_count, lexical_item_count, lexicalised_deprels_count

    def delexicalise_case_mark_cc(self, annotated_sentence):
        """
        This delexicalisation procedure involves, for each word,
        checking its dependency label; if it contains lexical information,
        search for its dependents, if the token has a 'case', 'mark' or 'cc' dependent,
        the enhanced label will be set to a placeholder label which
        will be reconstructed in a post-processing step.

        TODO: don't take ccomp deps
        """

        delexicalised_sentence = []
        
        # Operate on each token apart from ROOT
        for token in annotated_sentence[1:]:

            edeps = token.deps_set

            for i, edep in enumerate(edeps):
                enhanced_head = edep[0]
                enhanced_label = edep[1]

                # Likely a lexicalised head
                if len(enhanced_label.split(":")) >= 2:
                    if enhanced_label not in LONG_BASIC_LABELS:
                        self.lexicalised_deprels_count.update([f"{enhanced_label}"])

                        # Look at the token's children and see if they have modifiers which involve attaching a lemma.
                        for token_child in token.children:
                            token_child_edeps = token_child.deps_set
                            for token_child_edep in token_child_edeps:
                                token_child_enhanced_label = token_child_edep[1]

                                # 1) Token has a "case" dependent
                                if token_child_enhanced_label == "case":
                                    lexical_item = enhanced_label.split(":")[-1]
                                    delexicalised_edep = (enhanced_head, enhanced_label.replace(lexical_item, "<case_delex>"))
                                    edeps[i] = delexicalised_edep
                                    # update counters
                                    self.deprel_count.update(["case delexicalised"])
                                    self.lexical_item_count.update([lexical_item])

                                # 2) Token has a "mark" dependent
                                elif token_child_enhanced_label == "mark":
                                    lexical_item = enhanced_label.split(":")[-1]
                                    delexicalised_edep = (enhanced_head, enhanced_label.replace(lexical_item, "<mark_delex>"))
                                    edeps[i] = delexicalised_edep
                                    # update counters
                                    self.deprel_count.update(["mark delexicalised"])
                                    self.lexical_item_count.update([lexical_item])

                                # 3) Token has a "cc" dependent
                                elif token_child_enhanced_label == "cc":
                                    lexical_item = enhanced_label.split(":")[-1]
                                    delexicalised_edep = (enhanced_head, enhanced_label.replace(lexical_item, "<cc_delex>"))
                                    edeps[i] = delexicalised_edep
                                    # update counters
                                    self.deprel_count.update(["cc delexicalised"])
                                    self.lexical_item_count.update([lexical_item])

            # update token deps
            token.deps_set = edeps
            delexicalised_sentence.append(token)

        return delexicalised_sentence, self.deprel_count, self.lexical_item_count, self.lexicalised_deprels_count
                                
    def propagate_first_conj_labels(self, annotated_sentence):
        """
        See: "# text = Itinerary Both ships go to Caribbean Islands like Jamaica, Grand Cayman, Cozumel, St. Thomas, the Bahamas and St. Martin / St. Maarten."
        -> all tokens in a chain of conjs take the same label, and also attach the same cc label.

        Looks for tokens which are in conjunction with each other.
        We first look for the head of the conjoined phrase and append its (delexicalised) label to
        all of its conjuncts.

        """

        delexicalised_sentence = []

        seen_first_conj = False
        for token in annotated_sentence:
            edeps = token.deps_set
            for i, edep in enumerate(edeps):
                enhanced_head = edep[0]
                enhanced_label = edep[1]
                
                # Check if the token is a "conj" and inspect other tokens it is in conjunction with.
                base_relation = enhanced_label.split(":")[0]
                if base_relation == "conj":
                    first_conjunct_index = enhanced_head
                    
                    if not seen_first_conj:
                        #print("Propagating from first conjunct to all others.")
                        try:
                            first_conjunct_token = annotated_sentence[int(first_conjunct_index) -1]
                        except ValueError:
                            # For elided tokens, e.g. 5.1, we can scan through the ID column and look for the
                            # index which corresponds to the first_conjunct.
                            for token_index, token in enumerate(annotated_sentence):
                                if token.id == first_conjunct_index:
                                    first_conjunct_token = annotated_sentence[int(token_index)]

                        fct_children = first_conjunct_token.children
                        #print("Children of the first conjunct: ", fct_children)

                        fct_edeps = first_conjunct_token.deps_set
                        for i, edep in enumerate(fct_edeps):
                            #print(f"These are the labels to propagate {edep}")
                            # 7:nmod:<case_delex> -> 7:nmod
                            
                            tmp = []
                            tmp.append(enhanced_head)
                            tmp.append(enhanced_label.split(":")[:-1].pop())
                            fct_short = ":".join(tmp)
                            
                            print(fct_short)
                            #fct_long = ":".join(edep)

                            tmp_long = []
                            tmp_long.append(enhanced_head)
                            fct_long = enhanced_label
                            print(fct_long)
                            # 1) Pass first conjunct's head to all children with matching shorthand label
                            for fct_child in fct_children:
                                #print(f"Working on {fct_child}")
                                fct_child_edeps = fct_child.deps.split("|")
                                for i, edep in enumerate(fct_child_edeps):
                                    edep_short = ":".join(edep.split(":")[:-1])
                                    # if the shortened edep has the same label as the first conjunct, take its delexicalised label.
                                    if fct_short == edep_short: # TODO: Can the a word have two heads with same label?
                                        #print(f"Found matching labels {fct_short} --> {edep_short}. Changing to {fct_long}")
                                        # replace edep item with the label of the first conjunct.
                                        raise ValueError
                                        edep = fct_long
                                        fct_child_edeps[i] = edep

                                # update child token deps
                                fct_child.deps= "|".join(fct_child_edeps)
                                # update counters
                                self.deprel_count.update(["first delexicalised conjunct propagated"])

                        # Just do this process once.
                        seen_first_conj = True
            delexicalised_sentence.append(token)

        for t in delexicalised_sentence:
            print(t)

        return delexicalised_sentence


    def propagate_cc_modifier_in_conjs(self, annotated_sentence):
        """
        For the last conjunct there is usually a 'cc' modifer, e.g. apples, bananas *and* oranges.
        This 'and' needs to be passed to the labels of the words which precede the last conjunct in the sequence.
        We need to ensure consistency between the labels we are propagating.
        """

        delexicalised_sentence = []

        seen_cc_modifier = False
        for token in annotated_sentence:
            edeps = token.deps.split("|")
            for i, edep in enumerate(edeps):
                enhanced_label = edep.split(":")[1:]
                
                # Check if the token is a "conj" and inspect other tokens it is in conjunction with.
                base_relation = enhanced_label[0]
                if base_relation == "conj":
                    first_conjunct_index = edep.split(":")[0]
                    
                    if not seen_cc_modifier:
                        print("Searching for cc modifier.")
                        try:
                            first_conjunct_token = annotated_sentence[int(first_conjunct_index) -1]
                        except ValueError:
                            # For elided tokens, e.g. 5.1, we can scan through the ID column and look for the
                            # index which corresponds to the first_conjunct.
                            for token_index, token in enumerate(annotated_sentence):
                                if token.id == first_conjunct_index:
                                    first_conjunct_token = annotated_sentence[int(token_index)]

                        fct_children = first_conjunct_token.children
                        print("Children of the first conjunct: ", fct_children)

                        # 1) Search through all of the grand-children of the FCT and see which one the 'cc' modifier is attached to
                        # then pass that delexicalised label to the other conjuncts.
                        for fct_child in fct_children:
                            for fct_grandchild in fct_child.children:
                                print(f"Working on {fct_grandchild}")
                                fct_grandchild_edeps = fct_grandchild.deps.split("|")
                                for i, edep in enumerate(fct_grandchild_edeps):
                                    fct_grandchild_enhanced_label = edep.split(":")[1:].pop()
                                    
                                    # Token has a "cc" dependent
                                    if fct_grandchild_enhanced_label == "cc":
                                        # alter the child's edeps
                                        print(fct_child.deps)
                                        for edep in fct_child.deps.split("|"):
                                            print(edep)
                                            if "<cc_delex>" in edep:
                                                # TODO: should we take everything but the head (even though the head is usually always the same)
                                                cc_to_propagate = edep
                                                seen_cc_modifier = True

                        # 2) Pass delexicalised label from last conjunct upwards
                        if seen_cc_modifier:
                            for fct_child in fct_children:
                                #print(f"Working on {fct_child}")
                                fct_child_edeps = fct_child.deps.split("|")
                                for i, edep in enumerate(fct_child_edeps):
                                    # skip head and lexical label
                                    edep_short = ":".join(edep.split(":")[1:-1])
                                    print(edep_short)
                                    # if the shortened edep has the same label as the first conjunct, take its delexicalised label.
                                    if edep_short == "conj":
                                        #print(f"Found matching labels {fct_short} --> {edep_short}. Changing to {fct_long}")
                                        # replace edep item with the label of the first conjunct.
                                        edep = cc_to_propagate
                                        fct_child_edeps[i] = edep

                                # update child token deps
                                fct_child.deps= "|".join(fct_child_edeps)
                                # update counters
                                self.deprel_count.update(["last delexicalised conjunct propagated"])

            delexicalised_sentence.append(token)

        return delexicalised_sentence


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
        output_delexicalised_sentences, deprel_count, lexical_item_count, lexicalised_deprels_count = delexicalise_conllu.delexicalise(input_annotated_sentences)

        write_output_file(args.input, output_delexicalised_sentences)

        # print(deprel_count)
        # print(lexical_item_count)
        # print(lexicalised_deprels_count)
        # print(output_delexicalised_sentences)
    
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))