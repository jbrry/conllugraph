# based on the C2L2 utils in https://github.com/CoNLL-UD-2017/C2L2/blob/master/cdparser_multi/io.py

from graph import ConlluToken, DependencyGraph

# set CoNLL-U columns as indices
ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC = range(10)


def read_conll(filename):
    """
    Reads an input CoNLL-U file and parses the various CoNLL-U features.

    Arguments:
        filename: relative path of input file.

    Returns:
        graphs: string of dependency representations of modifiers and heads.
    """

    def get_word(columns):
        """
        Arguments:
            columns: List containing the 10 CoNLL-U columns at a particular row.

        Returns:
            ConlluToken object for each word which enables accessing the word's fields.
        """
        return ConlluToken(columns[FORM], columns[LEMMA], columns[UPOS], columns[XPOS], columns[FEATS], columns[HEAD], columns[DEPREL], columns[DEPS], columns[MISC])


    def get_graph(graphs, words, tokens, edges):
        """
        Arguments:
            graphs: List of `graph` strings.
            words: List of `word` objects returned by the ConlluToken class.
            tokens: List to store MWTs.
            edges: List of tuples containing (h, m, r) items.
        """
        graph = DependencyGraph(words, tokens)
        for (h, d, r) in edges:
            # call the attach method in DependencyGraph
            graph.attach(h, d, r)
        graphs.append(graph)

    file = open(filename, "r")

    graphs = []
    words = []
    tokens = []
    edges = []

    sentence_start = False
    while True:
        line = file.readline()
        if not line:
            if len(words) > 0:
                get_graph(graphs, words, tokens, edges)
                # Clear lists for next sentence
                words, tokens, edges = [], [], []
            break
        line = line.rstrip("\r\n")

        # Handle sentence start boundaries
        if not sentence_start:
            # Skip comments
            if line.startswith("#"):
                continue
            # Start a new sentence
            sentence_start = True
        if not line:
            sentence_start = False
            if len(words) > 0:
                get_graph(graphs, words, tokens, edges)
                words, tokens, edges = [], [], []
            continue

        # Read next token/word
        columns = line.split("\t")

        # Skip empty nodes
        # TODO: will need to keep track of elided tokens in the future
        if "." in columns[ID]:
            continue

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
            edges.append((head, int(columns[ID]), columns[DEPREL].split(":")[0]))

            for word in words:
                print(word)
                print(word.upos)

    file.close()

    return graphs