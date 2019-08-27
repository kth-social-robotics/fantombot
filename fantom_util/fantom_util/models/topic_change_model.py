"""Prepare a model to ensure proper swiching of topics in a conversation"""
from collections import defaultdict

from fantom_util import DataHandler
from fantom_util.score_functions import hellinger_similarity
from fantom_util.file_io_util import *
from fantom_util.feature_extraction.specifications import (
    TOPIC_CHANGE_MODEL_FEATURES,
    CLEAN_LDA,
)


class TopicChangeModel(model):
    def __init__(self):

        self.dh = None
        self.model = None

    def prepare_data(self):
        """Instanciate a DataHandler to instance variable."""
        self.dh = DataHandler(TOPIC_CHANGE_MODEL_FEATURES, "utterance_hack", fresh=True)
        return

    def build(self):
        """Make dict of id -> lda representation of tree."""
        # Link all roots to list of all their ancestor utts
        roots_all_kids_utts = defaultdict(list)
        for root in self.dh.node_lookup_table[None]:

            def append_kids(node_id):
                roots_all_kids_utts[root].append(self.dh.id_utt(node_id))
                if len(self.dh.node_lookup_table[node_id]) > 0:
                    for kid_node in self.dh.node_lookup_table[node_id]:
                        return append_kids(kid_node)

            append_kids(root)

        # Link all roots to the lda rep of all their ancestors
        roots_lda = {}
        for key in roots_all_kids_utts.keys():
            to_lda = ""
            for utt_id in roots_all_kids_utts[key]:
                to_lda.append(self.dh.id_utt[utt_id])
            roots_lda[key] = LDA.extract_features(to_lda)
        self.model = roots_lda
        return

    def train(self):
        """Use fresh data from prepare, build and save."""
        self.prepare_data()
        self.build()
        return self.save_model()

    def save_model(self):
        """Save to s3 bucket as pickle."""
        return pickle_to_bucket(self.model, "fantom-util", "topic_change_model")

    def load_model(self):
        """Load from s3 bucket pickle into instance model variable."""
        self.model = unpickle_from_bucket("fantom-util", "topic_change_model")

    def infer(self, utterances):
        best_score = -1
        best_key = None
        utts = LDA.extract_features(utterance)
        for root in self.model.keys():
            ## this should probably be KLD
            score = hellinger_similarity(utts, self.model[root])
            if score > best_score:
                best_score = score
                best_key = root
        return best_key, best_score
