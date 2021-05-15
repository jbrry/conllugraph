# based on the C2L2 utils in https://github.com/CoNLL-UD-2017/C2L2/blob/master/cdparser_multi/io.py

from collections import defaultdict

from graph import ConlluToken

# set CoNLL-U columns as indices
ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC = range(10)


def read_conll(filename):
    """
    Reads an input CoNLL-U file and parses the various CoNLL-U features.

    Arguments:
        filename: relative path of input file.

    Returns:
        annotated_sentences: List of Lists where each list contains the ConlluToken objects
        for each token in a sentence.
    """

    def get_word(columns):
        """
        Arguments:
            columns: List containing the 10 CoNLL-U columns at a particular row.

        Returns:
            ConlluToken object for the row which enables accessing the word's fields.
        """
        return ConlluToken(columns[ID], columns[FORM], columns[LEMMA], columns[UPOS], columns[XPOS], columns[FEATS], columns[HEAD], columns[DEPREL], columns[DEPS], columns[MISC])

    def get_children(words):
        """
        Arguments:
            words: List of word objects
        """
        # skip ROOT
        words = words[1:]
        for word in words:
            parent_deps = word.deps_set
            
            for h_l_tuple in parent_deps:
                parent = h_l_tuple[0]
                # skip ROOT
                if parent != "0":
                    # As EUD sentences may contain elided tokens, e.g. 5.1, we can't directly access
                    # the token from the head ID, so we search for matching conllu_ids instead
                    for target_index, target_token in enumerate(words):
                        if target_token.conllu_id == parent:
                            parent_token = words[int(target_index)]

                    parent_token.children.add(word)
                    print(f"parent {parent}, children: {parent_token.children}")

    file = open(filename, "r")

    root = ConlluToken(0, '*ROOT*', '*ROOT*', 'ROOT-UPOS', 'ROOT-XPOS', '_', -1, 'rroot', '-1:rroot', '_')

    words = []
    tokens = []
    edges = []
    annotated_sentences = []
    
    sentence_index = 1
    comments = defaultdict(lambda: [])

    while True:
        line = file.readline()

        # Set sentence_start to True for start of file.
        sentence_start = True

        # End of file
        if not line:
            if len(words) > 0:
                get_children(words)
                annotated_sentences.append(words)
                words, tokens, edges = [], [], []
            break
        
        line = line.rstrip("\r\n") # individual lines without linebreaks

        if line.startswith("#"):
            if sentence_start == True:
                # append dummy root node
                words = [root]
            sentence_start = False
            comments[sentence_index].append(line.strip())

        # Sentence ends, process items and create empty lists for next sentence
        if not line:
            # reset sentence_start to True for next line
            sentence_start = True
            sentence_index += 1
            if len(words) > 0:
                get_children(words)
                annotated_sentences.append(words)
                words, tokens, edges = [], [], []

        # Normal UD Line
        columns = line.split("\t")
        if len(columns) == 10:
            words.append(get_word(columns))
            if columns[HEAD].isdigit():
                head = int(columns[HEAD])
            else:
                head = -1
            edges.append((head, columns[ID], columns[DEPREL].split(":")[0]))

    file.close()

    return annotated_sentences, comments