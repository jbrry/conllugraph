# uses boiler-plate code from: https://github.com/spyysalo/wiki-bert-pipeline/blob/master/scripts/udtokenize.py

import sys
import csv
import os.path
from conllugraph import ConlluGraph
from evaluate import EvaluateConllu


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('-g', '--gold', type=str,
    help='Gold CoNLL-U file.')
    ap.add_argument('-s', '--silver', type=str, 
    help='Silver (system) CoNLL-U file.')
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
    # get annotated sentences
    g_annotated_sentences = conllu_graph.build_dataset(args.gold)
    s_annotated_sentences = conllu_graph.build_dataset(args.silver)

    # build individual edges
    g_sentence_edges = conllu_graph.build_edges(g_annotated_sentences)
    s_sentence_edges = conllu_graph.build_edges(s_annotated_sentences)

    # evaluation
    g_evaluate_conllu = EvaluateConllu(args.attach_morphological_case, args.visualise)
    g_deprel_count, g_modifier_lemmas, g_morph_case = g_evaluate_conllu.evaluate(g_sentence_edges, g_annotated_sentences)
    
    # re-initialise
    s_evaluate_conllu = EvaluateConllu(args.attach_morphological_case, args.visualise)
    s_deprel_count, s_modifier_lemmas, s_morph_case = s_evaluate_conllu.evaluate(s_sentence_edges, s_annotated_sentences)



    def log_output(args, input_type, deprel_counts, modifier_lemmas):
        """ Log outputs of gold/system results. """

        filename = "case.csv"
        file_exists = os.path.isfile(filename)

        if input_type == "gold":
            print("\n***\nGOLD")
            print(args.gold, "\n")
            path = args.gold
        elif input_type == "system":
            print("\n***\nSYSTEM")
            print(args.silver, "\n")
            path = args.silver

        num_case_deprels = deprel_counts['case']
        print(f"number case deprels: {num_case_deprels}")
        for k in modifier_lemmas.keys():
            modifier_lemma = modifier_lemmas[k]
            percentage = modifier_lemma / num_case_deprels
            print(f"{k}: {modifier_lemma} ({percentage:.2f})%")

            if k == "case_attached":
                with open(filename, 'a', newline='') as file:
                    fieldnames = ['pathname', 'case_attached']
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow({'pathname': path, 'case_attached': percentage})
                    
    # log gold statistics
    log_output(args, "gold", g_deprel_count, g_modifier_lemmas)
    # log system statistics
    log_output(args, "system", s_deprel_count, s_modifier_lemmas)


    # perform some checks
    num_case_labels = g_deprel_count["case"]
    case_values = sum(x for x in g_modifier_lemmas.values())
    assert num_case_labels == case_values, f"some deprels are unaccounted for when considering the following cases {g_modifier_lemmas.keys()}"


    ##
    # TODO:
    # working with un-aligned files is tricky.
    # a workaround may include:
    # for each gold sentence, look for the phenomenom we are interested in (e.g. case dependent)
    # then iterate through the silver sentence until the corresponding item is found:
    # compare
    # reset at the next sentence
    ##

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))