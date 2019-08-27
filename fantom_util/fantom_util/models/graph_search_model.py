from fantom_util.models.graph_search import find_reply
from fantom_util.models.model import Model
from fantom_util.models.named_entity_model import NamedEntityModel
from fantom_util.feature_extraction.specifications import GRAPHSEARCH_MODEL_FEATURES


class GraphSearchModel(Model):
    """Build, train or load a model to get replies from graph search.

    Attributes:
    dh (DataHandler): Using GRAPHSEARCH_MODEL_FEATURES
    model (dict): contains two dicts lookup_table and utts_dict
    fe (FeatureExtractor): Using GRAPHSEARCH_INFERENCE_FEATURES
    """

    __name__ = "graph_search_model"

    def prepare_data(self):
        """Instanciate a DataHandler to instance variable."""
        from fantom_util.data_handler import DataHandler

        self.dh = DataHandler(GRAPHSEARCH_MODEL_FEATURES, fresh=True)

    def build(self, fresh=False):
        """Link lookup_table and utts_dict to instance variable model."""
        nem = NamedEntityModel(self.stage)
        nem.load_model()
        print("named_entity_model", nem.model)
        self.model = {
            "lookup_table": self.dh.node_lookup_table,
            "node_utts": self.dh.node_utts,
            "id_utt": self.dh.id_utt,
            "named_entity_model": nem.model,
            "node_visit_counts": self.dh.node_visit_counts,
            "linked_nodes": self.dh.linked_nodes,
        }
        return

    def infer(self, utterance, history, in_root_node, blocked_children):
        """Generate a reply from the GraphSearch algorithm.

        Args:
            utterance (dict): containing all the input
            history (int): int of last visited system ids
            in_root_node (int): id of current root node
            blocked_children (list): ids of currently blocked children
            
        Returns:
            history (list): list of visited system ids
            response (string): the system response
            score (double): similarity measure between -1,1
        """
        return find_reply(
            self.model, utterance, history, in_root_node, blocked_children
        )

    def add_node(self, parent_id, utterance):
        # gen valid utt_id
        utt_id = max(self.model["id_utt"].keys()) + 70001
        # generate valid node_id
        node_id = max(self.model["node_utts"].keys()) + 70001

        self.model["lookup_table"][parent_id].append(node_id)
        self.model["node_utts"][node_id].append(utt_id)
        self.model["id_utt"][utt_id] = utterance

        return (
            node_id,
            (
                "Created node with:\n",
                "parent id: ",
                parent_id,
                "text: ",
                utterance["text"],
            ),
        )

