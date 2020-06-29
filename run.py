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
    ap.add_argument('-s', '--system', type=str, 
    help='System CoNLL-U file.')
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


def log_output(args, input_type, deprel_counts, modifier_lemmas):
    """ Prints outputs of gold/system results. """
    
    # in some cases, the parser may not have had any success
    has_attached_a_case_dependent = False

    if input_type == "gold":
        print("\n***\nGOLD")
        print(args.gold, "\n")
    elif input_type == "system":
        print("\n***\nSYSTEM")
        print(args.system, "\n")

    num_case_deprels = deprel_counts['case']
    print(f"number case deprels: {num_case_deprels}")
    for k in modifier_lemmas.keys():
        modifier_lemma = modifier_lemmas[k]
        percentage = modifier_lemma / num_case_deprels
        print(f"{k}: {modifier_lemma} ({percentage:.2f})%")
        if k == "case_attached":
            has_attached_a_case_dependent = True
            case_success = percentage

    if not has_attached_a_case_dependent:
        case_success = 0.
    
    return case_success


def main(argv):
    args = argparser().parse_args(argv[1:])

    conllu_graph = ConlluGraph()

    if args.gold:
        base_gold = os.path.basename(args.gold)
        g_annotated_sentences = conllu_graph.build_dataset(args.gold)
        g_sentence_edges = conllu_graph.build_edges(g_annotated_sentences)
        g_evaluate_conllu = EvaluateConllu(args.attach_morphological_case, args.visualise)
        g_deprel_count, g_modifier_lemmas, g_morph_case = g_evaluate_conllu.evaluate(g_sentence_edges, g_annotated_sentences)
        case_success_gold = log_output(args, "gold", g_deprel_count, g_modifier_lemmas)

    if args.system:
        base_system = os.path.basename(args.system)
        s_annotated_sentences = conllu_graph.build_dataset(args.system)
        s_sentence_edges = conllu_graph.build_edges(s_annotated_sentences)
        s_evaluate_conllu = EvaluateConllu(args.attach_morphological_case, args.visualise)
        s_deprel_count, s_modifier_lemmas, s_morph_case = s_evaluate_conllu.evaluate(s_sentence_edges, s_annotated_sentences)
        case_success_system = log_output(args, "system", s_deprel_count, s_modifier_lemmas)

    if args.gold and args.system:
        gold_tbid = base_gold.split("-")[0]
        system_tbid = base_system.split("-")[0]
        assert gold_tbid == system_tbid, "error: comparing gold and system from different tbids"

        header = ["tbid", "case_success_gold", "case_success_system", "diff_success"]
        row = []
        diff_success = case_success_gold - case_success_system
        row.append([gold_tbid, case_success_gold, case_success_system, diff_success])
        filename = "case.csv"
        file_exists = os.path.isfile(filename)

        csv_file = open(filename, 'a+', newline ='') 
        with csv_file:
            writer = csv.writer(csv_file) 
            if not file_exists:
                writer.writerow(header)
            writer.writerows(row)


    # perform some checks
    num_case_labels = g_deprel_count["case"]
    case_values = sum(x for x in g_modifier_lemmas.values())
    assert num_case_labels == case_values, f"some deprels are unaccounted for when considering the following cases {g_modifier_lemmas.keys()}"


    ##
    # TODO:
    # working with un-aligned files is tricky.
    # a workaround may include:
    # for each gold sentence, look for the phenomenom we are interested in (e.g. case dependent)
    # then iterate through the system sentence until the corresponding item is found:
    # compare
    # reset at the next sentence
    ##

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))