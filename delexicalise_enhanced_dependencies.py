import sys
import os.path
from collections import Counter

from conllugraph import ConlluGraph
from graph import stitch_edeps_items, unstitch_edeps_items

LONG_BASIC_LABELS=[
    "nmod:poss",
    "nsubj:pass",
    "nsubj:xsubj",
    "acl:relcl",
    "aux:pass",
    "compound:prt",
    "obl:npmod",
    "det:predet",
    "nmod:npmod",
    "cc:preconj"
    ] # Add any more or get this from a Vocab file

"""
Sample sentences:
# text = Because the US and Pakistan have managed to capture or kill about 2/3s of the top 25 al-Qaeda commanders, the middle managers are not in close contact with al-Zawahiri and Bin Laden.
# text = I didn't either until I clicked on the down button and they popped up.
# text = Various mitigating actions have been and will be taken to provide focus, gain comfort over control levels and to provide assurance to senior management as to the accuracy of the Q1 DPR and business balance sheet.
"""

def write_output_file(input_path, delexicalised_sentences, comment_lines):
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
        for sentence_information, sent in zip(comment_lines.values(), delexicalised_sentences):
            for line in sentence_information:
                fo.write(line + "\n") 

            for conllu_token in sent:
                fo.write(str(conllu_token) + "\n")
                #print(str(conllu_token))
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
        
            # Delexicalise enhanced relations which involve 'case', 'mark' and 'cc' dependents.
            delexicalised_sentence, deprel_count, lexical_item_count, \
                lexicalised_deprels_count = self.delexicalise_case_mark_cc(annotated_sentence)
            # We have delexicalised the labels where tokens have certain modifiers,
            # but we still need to make sure these are applied to conjs which do not have direct
            # modifiers, so they have to get their delexicalised label from the first conjunct.
            delexicalised_sentence = self.propagate_first_conj_labels(delexicalised_sentence)
            # Now propagate 'cc' modifier to all conjuncts
            delexicalised_sentence = self.propagate_cc_modifier_in_conjs(delexicalised_sentence)

            output_delexicalised_sentences.append(delexicalised_sentence)

        return output_delexicalised_sentences, deprel_count, lexical_item_count, lexicalised_deprels_count

    def delexicalise_case_mark_cc(self, annotated_sentence):
        """
        This delexicalisation procedure involves:
        For each word, checking its dependency label; if it contains lexical information,
        search for its dependents, if the token has a 'case', 'mark' or 'cc' dependent,
        the enhanced label will be set to a placeholder label denoting the type of modifier
        which will be reconstructed in a post-processing step.
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
                        lexical_item = enhanced_label.split(":")[-1]

                        # Look at the token's children and see if they have modifiers which involve attaching a lemma.
                        for token_child in token.children:
                            token_child_edeps = token_child.deps_set
                            for token_child_edep in token_child_edeps:
                                token_child_enhanced_label = token_child_edep[1]

                                # 1) Token has a "case" dependent
                                if token_child_enhanced_label == "case":
                                    if enhanced_label.split(":")[0] != "conj":
                                        delexicalised_edep = (enhanced_head, enhanced_label.replace(lexical_item, "<case_delex>"))
                                        edeps[i] = delexicalised_edep
                                        # update counters
                                        self.deprel_count.update(["case delexicalised"])
                                        self.lexical_item_count.update([lexical_item])

                                # 2) Token has a "mark" dependent
                                elif token_child_enhanced_label == "mark":
                                    if enhanced_label.split(":")[0] != "conj":
                                        delexicalised_edep = (enhanced_head, enhanced_label.replace(lexical_item, "<mark_delex>"))
                                        edeps[i] = delexicalised_edep
                                        # update counters
                                        self.deprel_count.update(["mark delexicalised"])
                                        self.lexical_item_count.update([lexical_item])

                                # 3) Token has a "cc" dependent but only append the lemma if the edep is "conj"
                                elif token_child_enhanced_label == "cc":
                                    if enhanced_label.split(":")[0] == "conj":
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
        Search for the head of the conjoined phrase and append its (delexicalised) label to
        all of its conjuncts.
        """

        delexicalised_sentence = []
        visited_conjuncts = set()
        possible_duplicates = []

        for token in annotated_sentence:
            edeps = token.deps_set
            for i, edep in enumerate(edeps):
                enhanced_head = edep[0]
                enhanced_label = edep[1]
                
                # Check if the token is a "conj" and inspect other tokens it is in conjunction with.
                base_relation = enhanced_label.split(":")[0]
                if base_relation == "conj":
                    first_conjunct_index = enhanced_head
                    # As EUD sentences may contain elided tokens, e.g. 5.1, we can't directly access
                    # the token from the head ID, so we search for matching conllu_ids instead 
                    for target_index, target_token in enumerate(annotated_sentence):
                        if target_token.conllu_id == first_conjunct_index:
                            first_conjunct_token = annotated_sentence[int(target_index)]


                    fct_children = first_conjunct_token.children
                    
                    fct_edeps = first_conjunct_token.deps_set
                    for i, edep in enumerate(fct_edeps):
                        # Get the base relation of the FCT and check the FCT's children to see if they share the same label.                     
                        fct_edep = stitch_edeps_items(edep)
                        # We are only concerned with propagating lexicalised labels
                        # >= 3 here because the stitched edep also includes the head.
                        if len(fct_edep.split(":")) >= 3:
                            # 1) Pass first conjunct's enhanced label to all children with matching shorthand label
                            for fct_child in fct_children:
                                # make sure we are doing this just once for every child of the first conjunct
                                if fct_child.conllu_id not in visited_conjuncts:
                                    fct_child_edeps = fct_child.deps_set
                                    for i, edep in enumerate(fct_child_edeps):
                                        fct_child_edep = stitch_edeps_items(edep)
                                        # if the shortened edep has the same label as the first conjunct, take its delexicalised label.
                                        if fct_edep.split(":")[:-1] == fct_child_edep.split(":")[:-1]:
                                            #print(f"{fct_edep.split(':')[:-1]} = {fct_child_edep.split(':')[:-1]}")
                                            # set edep to that of the FCT's
                                            edep = fct_edep
                                            fct_child_edeps[i] = unstitch_edeps_items(edep)

                                    # update child token deps
                                    fct_child.deps_set = fct_child_edeps
                                    # make sure the edeps are changed just once as each time a conjunct is encountered
                                    # it will process all conjs in the chain
                                    visited_conjuncts.add(fct_child.conllu_id)
                                    possible_duplicates.append(fct_child.conllu_id)
                                    # update counters
                                    self.deprel_count.update(["first delexicalised conjunct propagated"])

            delexicalised_sentence.append(token)

        # update token deps
        if len(visited_conjuncts) > 0:
            if len(visited_conjuncts) != len(possible_duplicates):
                raise ValueError("A token's deps was modified more than once!")

        return delexicalised_sentence


    def propagate_cc_modifier_in_conjs(self, annotated_sentence):
        """
        For the last conjunct there is usually a 'cc' modifer, e.g. apples, bananas and oranges.
        This 'and' needs to be passed to the labels of the words which precede the last conjunct in the sequence.
        """

        delexicalised_sentence = []
        visited_conjuncts = set()
        possible_duplicates = []

        seen_cc_modifier = False

        for token in annotated_sentence:
            edeps = token.deps_set
            for i, edep in enumerate(edeps):
                enhanced_head = edep[0]
                enhanced_label = edep[1]
                
                # Check if the token is a "conj" and inspect other tokens it is in conjunction with.
                base_relation = enhanced_label.split(":")[0]
                if base_relation == "conj":
                    first_conjunct_index = enhanced_head
                    
                    #if not seen_cc_modifier:
                    # As EUD sentences may contain elided tokens, e.g. 5.1, we can't directly access
                    # the token from the head ID, so we search for matching conllu_ids instead
                    for target_index, target_token in enumerate(annotated_sentence):
                        if target_token.conllu_id == first_conjunct_index:
                            first_conjunct_token = annotated_sentence[int(target_index)]

                    fct_children = first_conjunct_token.children
                    # 1) Search through all of the grandchildren of the FCT and see which one the 'cc' modifier is attached to
                    # then pass that delexicalised label to the other conjuncts.
                    for fct_child in fct_children:
                        for fct_grandchild in fct_child.children:
                            fct_grandchild_edeps = fct_grandchild.deps_set
                            for i, edep in enumerate(fct_grandchild_edeps):
                                fct_grandchild_enhanced_label = edep[1]
                                # If the token has a "cc" dependent, then it should have already been delexicalised. 
                                if fct_grandchild_enhanced_label == "cc":
                                    for edep in fct_child.deps_set:
                                        if "<cc_delex>" in edep[1]:
                                            # TODO: should we take everything but the head (even though the head is usually always the same)?
                                            cc_to_propagate = edep[1]
                                            seen_cc_modifier = True

                        # 2) Now that we have found a cc modifier, traverse the conj chain and use that label.
                        if seen_cc_modifier:
                            for fct_child in fct_children:
                                if fct_child.conllu_id not in visited_conjuncts:
                                    fct_child_edeps = fct_child.deps_set
                                    for i, edep in enumerate(fct_child_edeps):
                                        # skip head and lexical label
                                        edep_short = edep[1].split(":")[0]
                                        # if the edep is also a conj
                                        if edep_short == "conj":
                                            print(f"edep: {edep} last cc: {cc_to_propagate}")
                                            # replace the label with the last conj's cc dependent
                                            edep = (edep[0], edep[1].replace(edep[1], cc_to_propagate))
                                            fct_child_edeps[i] = edep

                                    # update child token deps
                                    fct_child.deps_set = fct_child_edeps
                                    # make sure the edeps are changed just once as each time a conjunct is encountered
                                    # it will process all conjs in the chain
                                    visited_conjuncts.add(fct_child.conllu_id)
                                    possible_duplicates.append(fct_child.conllu_id)
                                    # update counters
                                    self.deprel_count.update(["last delexicalised conjunct propagated"])

            delexicalised_sentence.append(token)
        
        # update token deps
        if len(visited_conjuncts) > 0:
            if len(visited_conjuncts) != len(possible_duplicates):
                raise ValueError("A token's deps was modified more than once!")
        
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
        input_annotated_sentences, comment_lines = conllu_graph.build_dataset(args.input)
        input_sentence_edges = conllu_graph.build_edges(input_annotated_sentences)

        delexicalise_conllu = DelexicaliseConllu(args.attach_morphological_case, args.visualise)
        output_delexicalised_sentences, deprel_count, lexical_item_count, lexicalised_deprels_count = delexicalise_conllu.delexicalise(input_annotated_sentences)

        write_output_file(args.input, output_delexicalised_sentences, comment_lines)

        # print(deprel_count)
        # print(lexical_item_count)
        # print(lexicalised_deprels_count)
        # print(output_delexicalised_sentences)
    
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))