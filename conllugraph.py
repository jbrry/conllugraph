from utils import read_conll

class ConlluGraph:
    def __init__(self):
        """ ConlluGraph. """
        pass

    def build_dataset(self, filename):
        print("Building dataset using {}".format(filename))
        graphs = read_conll(filename)
        return graphs
