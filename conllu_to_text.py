import sys
import re
import os.path
from collections import Counter

from conllugraph import ConlluGraph
from graph import stitch_edeps_items, unstitch_edeps_items


# def write_output_file(input_path, output_sentences):
#     """
#     Takes an input path and the relexicalsed sentences and writes them to an output
#     file in CoNLL-U format.
#     """

#     dirname = os.path.dirname(input_path)
#     basename = os.path.basename(input_path)
#     basename = re.sub(".conllu", ".txt", basename)

#     print(basename)

#     parent_dirs = dirname.split("/")
#     train_dev_path = parent_dirs[-2]
#     train_dev_path = train_dev_path + "-to-misc"
#     parent_dirs[-2] = train_dev_path
#     output_path = parent_dirs
#     output_path = "/".join(output_path)

#     if not os.path.exists(output_path):
#         print(f"Creating output path {output_path}")
#         os.makedirs(output_path)

#     outfile = os.path.join(output_path, basename)
#     with open(outfile, 'w', encoding='utf-8') as fo:
#         for sent in output_sentences:
#             output_sent = " ".join(sent)
#             #print(output_sent)
#             for conllu_token in output_sent:
#                 fo.write(str(conllu_token))
#             fo.write("\n")


def write_output_file(input_path, output_sentences, comment_lines):
    """
    Takes an input path and the delexicalsed sentences and writes them to an output
    file in CoNLL-U format.
    """

    dirname = os.path.dirname(input_path)
    basename = os.path.basename(input_path)

    parent_dirs = dirname.split("/")
    train_dev_path = parent_dirs[-2]
    train_dev_path = train_dev_path + "-pred-to-misc" # "-gold-to-plainsen" #"-pred-to-misc" "-gold-to-pretok"
    parent_dirs[-2] = train_dev_path
    output_path = parent_dirs
    output_path = "/".join(output_path)

    if not os.path.exists(output_path):
        print(f"Creating output path {output_path}")
        os.makedirs(output_path)

    outfile = os.path.join(output_path, basename)
    with open(outfile, 'w', encoding='utf-8') as fo:

       for sentence_information, sent in zip(comment_lines.values(), output_sentences):
            # write comments if necessary
            # for line in sentence_information:
            #     fo.write(line + "\n") 

            # PLAINSEN
            # output_sent = " ".join(sent)
            # for conllu_line in output_sent:
            #     fo.write(str(conllu_line))
            # fo.write("\n")

            # PRETOK
            # for conllu_token in sent:
            #     #fo.write(conllu_token.word + "\n")
            #     fo.write(conllu_token + "\n") # pretok
            #     #print(str(conllu_token))
            # fo.write("\n")

            # CONLLU
            for conllu_token in sent:
                fo.write(str(conllu_token) + "\n")
                #print(str(conllu_token))
            fo.write("\n")



class CopyConllu(object):
    def __init__(self):
        pass


    def copy(self, input_annotated_sentences, input_secondary_annotated_sentences):
        """ """

        output_sentences = []






        return output_sentences

    def conllu_to_text(self, input_annotated_sentences):

        output_sentences = []

        for annotated_sentence in input_annotated_sentences:
            output_sentence = []
            for token in annotated_sentence[1:]:
                if "-" in token.conllu_id:
                    continue

                # if there is a space, replace it with placeholder so we don't split on it
                if " " in token.word:
                    new_token = re.sub(" ", "@SPACE@", token.word)
                    #print(token.word, new_token)
                    token.word = new_token

                output_sentence.append(token.word)
            output_sentences.append(output_sentence)

        return output_sentences

    def copy_to_pretok(self, input_annotated_sentences):

        output_sentences = []
        
        for annotated_sentence in input_annotated_sentences:
            output_sentence = []
            for token in annotated_sentence[1:]:
                output_sentence.append(token.word)
            output_sentences.append(output_sentence)

        return output_sentences


    def copy_basic_to_misc(self, input_annotated_sentences, input_secondary_annotated_sentences):
        """copy basic tree to misc column"""

        output_sentences = []

        for input_annotated_sentence, input_secondary_annotated_sentence in zip(input_annotated_sentences, input_secondary_annotated_sentences):

            output_sentence = []
            pred_annotations = []


            if len(input_annotated_sentence[1:]) != len(input_secondary_annotated_sentence):
                print("WARNING")
                print(input_annotated_sentence[1:])
                print()
                print(input_secondary_annotated_sentence)
                #raise ValueError

            # get all pred labels in the right format;
            for pred_token in input_secondary_annotated_sentence:
                head = pred_token.head
                label = pred_token.deprel
                head_2_misc = f"Head={head}|Label={label}"
                pred_annotations.append(head_2_misc)

        
            # now copy pred to gold
            for gold_token, head_2_misc in zip(input_annotated_sentence[1:], pred_annotations):
                #print(gold_token.conllu_id)
                gold_token.misc = head_2_misc
                output_sentence.append(gold_token)

            assert len(output_sentence) == len(pred_annotations), f"{len(output_sentence)} != {len(pred_annotations)}"

            output_sentences.append(output_sentence)

            

        
        return output_sentences


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('-i', '--input', type=str,
    help='Input CoNLL-U file.')
    ap.add_argument('-s', '--secondary-input', type=str,
    help='Input (secondary) CoNLL-U file.')
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

    # Copy GOLD TO PRETOK/PLAINSEN
    # if args.input:
    #     base_input = os.path.basename(args.input)
    #     input_annotated_sentences, input_vocab, input_comment_lines = conllu_graph.build_dataset(args.input)
    #     input_sentence_edges = conllu_graph.build_edges(input_annotated_sentences)    

    #     copy_conllu = CopyConllu()
    #     output_sentences = copy_conllu.conllu_to_text(input_annotated_sentences)
    #     print(output_sentences[0:10])

    #     write_output_file(args.input, output_sentences, input_comment_lines)


    # COPY BASIC TO MISC
    if args.input and args.secondary_input:
        base_input = os.path.basename(args.input)
        input_annotated_sentences, input_vocab, input_comment_lines = conllu_graph.build_dataset(args.input)
        input_sentence_edges = conllu_graph.build_edges(input_annotated_sentences)

        base_secondary_input = os.path.basename(args.secondary_input)
        input_secondary_annotated_sentences, vocab, comment_lines = conllu_graph.build_dataset(args.secondary_input)
        input_secondary_sentence_edges = conllu_graph.build_edges(input_secondary_annotated_sentences)

        copy_conllu = CopyConllu()
        output_sentences = copy_conllu.copy_basic_to_misc(input_annotated_sentences, input_secondary_annotated_sentences)
        print(output_sentences[0:10])

        write_output_file(args.input, output_sentences, input_comment_lines)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))