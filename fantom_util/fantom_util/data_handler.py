import sys
from collections import defaultdict

from fantom_util.feature_extraction.feature_extractor import FeatureExtractor
from fantom_util.database import db_session
from fantom_util.database.models import Node, LinkedNodes
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from tqdm import tqdm


class DataHandler(object):
    """Import, export, process and have ready access to data.

    Attributes:
    data_id (string): key of data in database
    fe (FeatureExtractor): features spec in __init__
    dialogs (generator): of geneators of utts containing all dialogs
    utts_list (list): of utts loaded from the database
    lookup_table (dict): on the form {'parent_id': list of ids}
    utts_dict (dict): on the form {'id': utterance dict}
    """

    def __init__(self, features, data_id=None, fresh=False):
        """Prepare attributes."""

        self.data_id = data_id

        self.fe = FeatureExtractor(features)

        self.node_lookup_table, self.node_utts, self.id_utt, self.node_visit_counts, self.linked_nodes = DataHandler.prepare_from_db()

        for key in tqdm(self.id_utt):
            try:
                self.id_utt[key] = self.process_utterance(self.id_utt[key])
            except:
                print('ERROR')
                for row in sys.exc_info()[-7:]:
                    print(row)
                print(
                    'On the utterance id: ',
                    f'{key}, utterance: {self.id_utt[key]}'
                )

    @staticmethod
    def prepare_from_db():
        nodes = db_session \
            .query(Node) \
            .options(joinedload(Node.utterances)) \
            .filter(
            Node.active.is_(True),
            or_(Node.visited_count > 1, Node.child_count > 0, Node.is_user.is_(False))
        ) \
            .all()
        lookup_table = defaultdict(list)
        node_utts = defaultdict(list)
        node_visit_counts = {}
        id_utt = {}

        for node in nodes:
            lookup_table[node.parent_id].append(node.id)
            node_visit_counts[node.id] = node.visited_count
            for utterance in node.utterances:
                node_utts[node.id].append(utterance.id)
                id_utt[utterance.id] = {'text': utterance.utterance_text}

        linked_nodes = {from_node: to_node
                        for from_node, to_node
                        in db_session.query(LinkedNodes.linked_from_node_id, LinkedNodes.linked_to_node_id).all()}

        return lookup_table, node_utts, id_utt, node_visit_counts, linked_nodes

    def process_utterance(self, row):
        """Take a dict and provide features from FeatureExtractor"""
        return self.fe(row)

    def process_dialog(self, dialog):
        """Take a dialog generator and provide features from FeatureExtractor"""
        return (self.process_utterance(row) for row in dialog)

    def process_dialogs(self, dialogs):
        """Take a dialogs generator and provide features from FeatureExtractor"""
        return (self.process_dialog(dialog) for dialog in dialogs)
