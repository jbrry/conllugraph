# based on the classes in: https://github.com/CoNLL-UD-2017/C2L2/blob/master/cdparser_multi/graph.py
# https://github.com/ftyers/ud-scripts/blob/e6d2771719c479b3be6e7a884a128def46d4b987/conllu-lift.py

import re
import numpy as np


def parse_features(features):
    """
    Parses the token's morphological features.

    Arguments:
        features: the unprocessed morphological features.
    
    Returns:
        features_dict: a dictionary with separated morphological features.
    """
    
    features_dict = {}

    if features == "_":
        return

    split_features = features.split("|")
    for feature in split_features:
        parts = feature.split('=')
        features_dict[parts[0]] = parts[1]

    return features_dict


def parse_deps(deps):
    """
    Parses the token's deps features.

    Arguments:
        deps: the unprocessed deps features.
    
    Returns:
        parsed_deps: a list of tuples of parsed edeps for each token.
        [('11', 'acl:relcl'), ('15', 'conj:and')]
    """
    parsed_deps = []

    for edep in deps.split("|"):
        if edep == "_" or not edep:
            continue
        parts = edep.split(":")
        enhanced_head = parts[0]
        tail = parts[1:]
        # stitch the remaining parts together again
        enhanced_deprel = ":".join(tail)
        parsed_edep = (enhanced_head, enhanced_deprel)
        parsed_deps.append(parsed_edep)

    return parsed_deps


class ConlluToken:
    """
    ConlluToken

    Store each CoNLL-U attribute per token.
    """
    def __init__(self,
                id = None,
                word = None,
                lemma = None,
                upos = None,
                xpos = None,
                feats = None,
                head = None,
                deprel = None,
                deps = None,
                misc = None):
        
        self.id = id
        self.word = word
        self.lemma = lemma if lemma else "_"
        self.upos = upos if upos else "_"
        self.xpos = xpos if xpos else "_"
        self.feats = feats if feats else "_"
        self.feats_set = parse_features(self.feats)
        self.head = head if head else "_"
        self.deprel = deprel if deprel else "_"
        self.deps = deps if deps else "_"
        #print(self.deps)
        self.deps_parsed = parse_deps(self.deps)    
        self.misc = misc if misc else "_"

    def cleaned(self):
        return ConlluToken(self.word, "_")

    def clone(self):
        return ConlluToken(self.id, self.word, self.lemma, self.upos, self.xpos, self.feats, self.head, self.deprel, self.deps, self.misc)

    def __str__(self):
        return str(self.word)

    def __repr__(self):
        #return "{}_{}_{}|||{}".format(self.word, self.deprel, self.head, self.deps)
        return self.word


class DependencyGraph(object):
    """
    DependencyGraph
    """
    def __init__(self, words, tokens=None):
        #  Token is a tuple (start, end, form)
        if tokens is None:
            tokens = []
        self.nodes = np.array([ConlluToken("*ROOT*", "*ROOT*")] + list(words))
        self.tokens = tokens
        self.heads = np.array([-1] * len(self.nodes))
        self.rels = np.array(["_"] * len(self.nodes), dtype=object)

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.nodes = self.nodes
        result.tokens = self.tokens
        result.heads = self.heads.copy()
        result.rels = self.rels.copy()
        return result

    def cleaned(self, node_level=True):
        if node_level:
            return DependencyGraph([node.cleaned() for node in self.nodes[1:]], self.tokens)
        else:
            return DependencyGraph([node.clone() for node in self.nodes[1:]], self.tokens)

    def attach(self, head, tail, rel):
        self.heads[tail] = head
        self.rels[tail] = rel

    def __repr__(self):
        # word_representation -> deprel head head_word_representation
        # they_PRON ->(nsubj)  21 (performed_VERB)
        return "\n".join(["{} ->({})  {} ({})".format(str(self.nodes[i]), self.rels[i], self.heads[i], self.nodes[self.heads[i]]) for i in range(len(self.nodes))])
