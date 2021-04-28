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
        for word in words[1:]:
            try:
                parent = words[int(word.head)]
                # don't append children for notional ROOT
                if parent.id != "0":
                    parent.children.append(word)
            except ValueError:
                # Elided token
                continue

    file = open(filename, "r")

    root = ConlluToken(0, '*ROOT*', '*ROOT*', 'ROOT-UPOS', 'ROOT-XPOS', '_', -1, 'rroot', '-1:rroot', '_')

    words = []
    tokens = []
    edges = []
    comments = defaultdict(lambda: [])
    sentence_index = 1
    annotated_sentences = []

    sentence_start = False
    while True:
        line = file.readline()
        # end of file
        if not line:
            if len(words) > 0:
                get_children(words)
                annotated_sentences.append(words)
                words, tokens, edges = [], [], []
            break
        line = line.rstrip("\r\n")

        # Handle sentence start boundaries
        if not sentence_start:

            if line.startswith("#"):
                comments[sentence_index].append(line.strip())
                continue

            # Start a new sentence
            sentence_start = True
            sentence_index += 1
            # Append dummy ROOT to start of sentence
            words.append(root)
        if not line:
            sentence_start = False
            if len(words) > 0:
                get_children(words)
                annotated_sentences.append(words)
                words, tokens, edges = [], [], []
            continue

        # Read next token/word
        columns = line.split("\t")

        # Handle multi-word tokens to save word(s)
        if "-" in columns[ID]:
            start, end = map(int, columns[ID].split("-"))
            tokens.append((start, end + 1, columns[FORM]))

            for _ in range(start, end + 1):
                word_line = file.readline().rstrip("\r\n")
                word_columns = word_line.split("\t")
                words.append(get_word(word_columns))
                if word_columns[HEAD].isdigit():
                    head = int(word_columns[HEAD])
                else:
                    head = -1
                edges.append((head, int(word_columns[ID]), word_columns[DEPREL].split(":")[0]))
        # Regular tokens/words
        else:
            words.append(get_word(columns))
            if columns[HEAD].isdigit():
                head = int(columns[HEAD])
            else:
                head = -1
            edges.append((head, columns[ID], columns[DEPREL].split(":")[0]))

    file.close()

    return annotated_sentences, comments