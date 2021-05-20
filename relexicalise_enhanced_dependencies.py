import sys
import re
import os.path
from collections import Counter

from conllugraph import ConlluGraph
from graph import stitch_edeps_items, unstitch_edeps_items

LONG_BASIC_LABELS=[
    "nmod:poss",
    "nmod:tmod",
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

def write_output_file(input_path, relexicalised_sentences, comment_lines):
    """
    Takes an input path and the relexicalsed sentences and writes them to an output
    file in CoNLL-U format.
    """

    dirname = os.path.dirname(input_path)
    basename = os.path.basename(input_path)

    parent_dirs = dirname.split("/")
    train_dev_path = parent_dirs[-2]
    train_dev_path = train_dev_path + "-relexicalised"
    parent_dirs[-2] = train_dev_path
    output_path = parent_dirs
    output_path = "/".join(output_path)

    if not os.path.exists(output_path):
        print(f"Creating output path {output_path}")
        os.makedirs(output_path)

    outfile = os.path.join(output_path, basename)
    with open(outfile, 'w', encoding='utf-8') as fo:
        for sentence_information, sent in zip(comment_lines.values(), relexicalised_sentences):
            for line in sentence_information:
                fo.write(line + "\n") 

            for conllu_token in sent:
                fo.write(str(conllu_token) + "\n")
            fo.write("\n")


class RelexicaliseConllu(object):
    def __init__(self,
                attach_morphological_case,
                visualise
                ):
        """
        RelexicaliseConllu
        
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

    def relexicalise(self, annotated_sentences):
        """Perform various types of relexicalisation."""

        output_relexicalised_sentences = []

        for annotated_sentence in annotated_sentences:
        
            # Relexicalise enhanced relations which involve 'case', 'mark' and 'cc' dependents.
            relexicalised_sentence, deprel_count, lexical_item_count, \
                lexicalised_deprels_count = self.relexicalise_case_mark_cc(annotated_sentence)

            # We have delexicalised the labels where tokens have certain modifiers,
            # but we still need to make sure these are applied to conjs which do not have direct
            # modifiers, so they have to get their delexicalised label from the first conjunct.
            relexicalised_sentence = self.propagate_first_conj_labels(relexicalised_sentence)
            # Now propagate 'cc' modifier to all conjuncts
            relexicalised_sentence = self.propagate_cc_modifier_in_conjs(relexicalised_sentence)

            output_relexicalised_sentences.append(relexicalised_sentence)

        return output_relexicalised_sentences, deprel_count, lexical_item_count, lexicalised_deprels_count

    def relexicalise_case_mark_cc(self, annotated_sentence):
        """
        This relexicalisation procedure involves:
        For each word, checking its dependency label; if it contains delexicalised information,
        see what kind of delexicalised label the parser predicted,
        see if there is another word in the sentence with that label.
        search for its dependents, if the token has a 'case', 'mark' or 'cc' dependent,
        the enhanced label will be set to a placeholder label which
        will be reconstructed in a post-processing step.

        """

        relexicalised_sentence = []

        # Operate on each token apart from ROOT
        for token in annotated_sentence[1:]:
            edeps = token.deps_set
            for i, edep in enumerate(edeps):
                enhanced_head = edep[0]
                enhanced_label = edep[1]

                # 1) Relexicalise "case" placeholders
                if "<case_delex>" in enhanced_label:
                    for token_child in token.children:
                        token_child_edeps = token_child.deps_set
                        for token_child_edep in token_child_edeps:
                            token_child_enhanced_label = token_child_edep[1]
                            if token_child_enhanced_label == "case":
                                lexical_item = token_child.lemma
                                
                                # check again for fixed children and append to lexical item
                                for token_grandchild in token_child.children:
                                    token_grandchild_edeps = token_grandchild.deps_set
                                    for token_grandchild_edep in token_grandchild_edeps:
                                        token_grandchild_enhanced_label = token_grandchild_edep[1]
                                        if token_grandchild_enhanced_label == "fixed":
                                            lexical_item = f"{lexical_item}_{token_grandchild.lemma}"

                                parts = enhanced_label.split(":")
                                for j, part in enumerate(parts):
                                    relex_part = re.sub("<case_delex>", lexical_item, part)
                                    parts[j] = relex_part
                                enhanced_label = ":".join(parts)
                                relexicalised_edep = (enhanced_head, enhanced_label)

                                edeps[i] = relexicalised_edep
                                # update counters
                                self.deprel_count.update(["case relexicalised"])
                                self.lexical_item_count.update([lexical_item])

                # 2) Relexicalise "mark" placeholders
                if "<mark_delex>" in enhanced_label:
                    for token_child in token.children:
                        token_child_edeps = token_child.deps_set
                        for token_child_edep in token_child_edeps:
                            token_child_enhanced_label = token_child_edep[1]
                            if token_child_enhanced_label == "mark":
                                lexical_item = token_child.lemma

                                parts = enhanced_label.split(":")
                                for j, part in enumerate(parts):
                                    relex_part = re.sub("<mark_delex>", lexical_item, part)
                                    parts[j] = relex_part
                                enhanced_label = ":".join(parts)
                                relexicalised_edep = (enhanced_head, enhanced_label)
                                
                                edeps[i] = relexicalised_edep
                                # update counters
                                self.deprel_count.update(["mark relexicalised"])
                                self.lexical_item_count.update([lexical_item])

                # 3) Relexicalise "cc" placeholders
                if "<cc_delex>" in enhanced_label:
                    for token_child in token.children:
                        token_child_edeps = token_child.deps_set
                        for token_child_edep in token_child_edeps:
                            token_child_enhanced_label = token_child_edep[1]
                            if token_child_enhanced_label == "cc":
                                lexical_item = token_child.lemma

                                parts = enhanced_label.split(":")
                                for j, part in enumerate(parts):
                                    relex_part = re.sub("<cc_delex>", lexical_item, part)
                                    parts[j] = relex_part
                                enhanced_label = ":".join(parts)
                                relexicalised_edep = (enhanced_head, enhanced_label)
                                
                                edeps[i] = relexicalised_edep
                                # update counters
                                self.deprel_count.update(["cc relexicalised"])
                                self.lexical_item_count.update([lexical_item])

            # update token deps
            token.deps_set = edeps
            relexicalised_sentence.append(token)
        
        return relexicalised_sentence, self.deprel_count, self.lexical_item_count, self.lexicalised_deprels_count


    def propagate_first_conj_labels(self, annotated_sentence):
        """
        Tokens with "conj" labels will still have delexicalised placeholders as they rely on the first conjunct
        to get their delexicalised label.
        Search for the head of the conjoined phrase and append its (relexicalised) label to
        the label of the conjunct if there is a matching shorthand label.
        """

        relexicalised_sentence = []
        visited_conjuncts = set()
        possible_duplicates = []

        for token in annotated_sentence:
            edeps = token.deps_set
            for i, edep in enumerate(edeps):
                enhanced_head = edep[0]
                enhanced_label = edep[1]

                if "conj" in enhanced_label:     
                    first_conjunct_index = enhanced_head
                    # As EUD sentences may contain elided tokens, e.g. 5.1, we can't directly access
                    # the token from the head ID, so we search for matching conllu_ids instead 
                    for target_index, target_token in enumerate(annotated_sentence):
                        if target_token.conllu_id == first_conjunct_index:
                            first_conjunct_token = annotated_sentence[int(target_index)]             

                    # 1) Get the conj's parent's edeps and see if we can take the label from there
                    fct_edeps = first_conjunct_token.deps_set
                    for i, fct_edep in enumerate(fct_edeps):
                        fct_edep = stitch_edeps_items(fct_edep)

                        # Now scan back through our own edeps to see if we have a matching shorthand label
                        for i, edep in enumerate(edeps):
                            enhanced_head = edep[0]
                            enhanced_label = edep[1]
                            edep = stitch_edeps_items(edep)

                            if "delex" in enhanced_label:
                                delex_placeholder = enhanced_label.split(":")[-1]
                                # check for the same base relation (excluding head and lexical tail)
                                if fct_edep.split(":")[1:-1] == edep.split(":")[1:-1]:
                                    lexical_item = fct_edep.split(":")[-1]
                                    edep = (enhanced_head, enhanced_label.replace(delex_placeholder, lexical_item))
                                    edeps[i] = edep

                        token.deps_set = edeps
                        visited_conjuncts.add(token.conllu_id)
                        possible_duplicates.append(token.conllu_id)

                        self.deprel_count.update(["first relexicalised conjunct propagated"])

            relexicalised_sentence.append(token)

        # if len(visited_conjuncts) > 0:
        #     if len(visited_conjuncts) != len(possible_duplicates):
        #         raise ValueError("A token's deps was modified more than once!")
        
        return relexicalised_sentence


    def propagate_cc_modifier_in_conjs(self, annotated_sentence):
        """
        For the last conjunct there is usually a 'cc' modifer, e.g. apples, bananas and oranges.
        This 'and' needs to be passed to the labels of the words which precede the last conjunct in the sequence.
        """

        relexicalised_sentence = []
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

                    # only carry this out if there is a delexicalised label
                    if "delex" in enhanced_label:
                        first_conjunct_index = enhanced_head
                        
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
                                    # Token has a "cc" dependent
                                    if fct_grandchild_enhanced_label == "cc":
                                        lexical_item = fct_grandchild.lemma
                                        seen_cc_modifier = True


                        # 2) Now that we have found the cc modifier, traverse the conj chain and use that label.
                        if seen_cc_modifier:
                            for fct_child in fct_children:
                                fct_child_edeps = fct_child.deps_set
                                for i, edep in enumerate(fct_child_edeps):
                                    enhanced_head = edep[0]
                                    enhanced_label = edep[1]

                                    if "<cc_delex>" in enhanced_label:
                                        edep = (enhanced_head, enhanced_label.replace("<cc_delex>", lexical_item))
                                        fct_child_edeps[i] = edep

                                # update child token deps
                                fct_child.deps_set = fct_child_edeps
                                visited_conjuncts.add(token.conllu_id)
                                possible_duplicates.append(token.conllu_id)
                                
                                # update counters
                                self.deprel_count.update(["last delexicalised conjunct propagated"])

            relexicalised_sentence.append(token)

        #if len(visited_conjuncts) > 0:
        #    if len(visited_conjuncts) != len(possible_duplicates):
        #        raise ValueError("A token's deps was modified more than once!")

        return relexicalised_sentence


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
        input_annotated_sentences, vocab, comment_lines = conllu_graph.build_dataset(args.input)
        input_sentence_edges = conllu_graph.build_edges(input_annotated_sentences)

        relexicalise_conllu = RelexicaliseConllu(args.attach_morphological_case, args.visualise)
        output_relexicalised_sentences, deprel_count, lexical_item_count, lexicalised_deprels_count = relexicalise_conllu.relexicalise(input_annotated_sentences)

        write_output_file(args.input, output_relexicalised_sentences, comment_lines)

        # print(deprel_count)
        # print(lexical_item_count)
        # print(lexicalised_deprels_count)
        # print(output_delexicalised_sentences)
    
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))