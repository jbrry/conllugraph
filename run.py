# uses boiler-plate code from: https://github.com/spyysalo/wiki-bert-pipeline/blob/master/scripts/udtokenize.py

import sys
from conllugraph import ConlluGraph
from evaluate import EvaluateConllu


def argparser():
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('-i', '--input', type=str, 
    help='Input CoNLL-U file.')
    ap.add_argument('-g', '--gold', type=str,
    help='Gold CoNLL-U file.')
    ap.add_argument('-e', '--encoding', default='utf-8', type=str,
    help='Type of encoding.')
    ap.add_argument('-s', '--save-stats', metavar='FILE', default=None,
    help='Whether to save statistics.')
    ap.add_argument('-q', '--quiet', default=False, action='store_true',
    help='Do not display certain helper information.')
    return ap

def main(argv):
    args = argparser().parse_args(argv[1:])
    
    cg = ConlluGraph()
    # get annotated sentences
    graphs, annotated_sentences = cg.build_dataset(args.input)

    #    
    sentence_edges = cg.build_edges(annotated_sentences)

    # evaluation
    ec = EvaluateConllu()
    evaluated_edges = ec.evaluate(sentence_edges, annotated_sentences)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))