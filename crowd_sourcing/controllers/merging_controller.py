from collections import defaultdict
from fantom_util.constants import *
from fantom_util.feature_extraction.feature_extractor import FeatureExtractor
from fantom_util.feature_extraction.specifications import WORD_CLASS_SCORE
from fantom_util.misc import gen_feature_dict
from fantom_util.score_functions import graph_search_score
from fantom_util.database import db_session
from fantom_util.database.models import Node, Merging
from fantom_util.graph_tools.node_tools import merge_nodes
import logging
from sqlalchemy.orm import joinedload

logging.basicConfig(filename='db.log')
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def get_merge_nodes():
    merges = db_session.query(Merging).all()
    used_nodes = []
    vec_cache = {}
    node_pairs = []
    parent_ids = []

    for merge in merges:
        used_nodes.append(f'{merge.left_node_id}--{merge.right_node_id}')

    nodes = db_session.query(Node).options(joinedload(Node.utterances), joinedload(Node.node_utterances)).filter(Node.parent_id==None, Node.active == True).order_by(Node.parent_id.desc()).all()
    grouped_nodes = defaultdict(list)

    fe = FeatureExtractor(gen_feature_dict(WORD_CLASS_SCORE))

    for node in nodes:
        grouped_nodes[node.parent_id].append(node)
        if node.parent_id not in parent_ids:
            parent_ids.append(node.parent_id)

    for group, grouped_nodes in grouped_nodes.items():
        for i, left_node in enumerate(grouped_nodes):
            for j, right_node in enumerate(grouped_nodes):
                if i != j and f'{left_node.id}--{right_node.id}' not in used_nodes and f'{right_node.id}--{left_node.id}' not in used_nodes:
                    used_nodes.append(f'{left_node.id}--{right_node.id}')
                    node_info = {
                        'score': 0,
                        'left_node_id': left_node.id,
                        'right_node_id': right_node.id,
                        'parent_utterances': [x.utterance_text for x in left_node.parent.utterances] if left_node.parent else [],
                        'left_node_utterances': [],
                        'right_node_utterances': []
                    }
                    for left_utterance in left_node.utterances:
                        for right_utterance in right_node.utterances:
                            vec_1 = vec_cache.get(left_utterance)
                            vec_2 = vec_cache.get(right_utterance)

                            if not vec_1:
                                vec_1 = fe.extract_features({'text': left_utterance.utterance_text})
                                vec_cache[left_utterance] = vec_1

                            if not vec_2:
                                vec_2 = fe.extract_features({'text': right_utterance.utterance_text})
                                vec_cache[right_utterance] = vec_2

                            gss = graph_search_score(vec_1, vec_2)
                            score = gss if gss > 0 else 0

                            node_info['score'] = max(node_info['score'], score)
                            node_info['left_node_utterances'].append(left_utterance.utterance_text)
                            node_info['right_node_utterances'].append(right_utterance.utterance_text)
                    node_info['left_node_utterances'] = list(set(node_info['left_node_utterances']))
                    node_info['right_node_utterances'] = list(set(node_info['right_node_utterances']))
                    node_pairs.append(node_info)

    return sorted(node_pairs, key=lambda x: x['score'], reverse=True)
