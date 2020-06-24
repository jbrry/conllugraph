# uses boiler-plate code from: https://github.com/spyysalo/wiki-bert-pipeline/blob/master/scripts/udtokenize.py

import sys
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

    # log statistics
    print("\n***\nGOLD")
    print(args.gold, "\n")
    g_num_case_deprels = g_deprel_count['case']
    print(f"number case deprels: {g_num_case_deprels}")
    for gk in g_modifier_lemmas.keys():
        g_modifier_lemma = g_modifier_lemmas[gk]
        percentage = g_modifier_lemma / g_num_case_deprels
        print(f"{gk}: {g_modifier_lemma} ({percentage:.2f})%")

    print("\n***\nSYSTEM")
    print(args.silver, "\n")
    s_num_case_deprels = s_deprel_count['case']
    print(f"number case deprels: {s_num_case_deprels}")
    for sk in s_modifier_lemmas.keys():
        s_modifier_lemma = s_modifier_lemmas[sk]
        percentage = s_modifier_lemma / s_num_case_deprels
        print(f"{sk}: {s_modifier_lemma} ({percentage:.2f})%")

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