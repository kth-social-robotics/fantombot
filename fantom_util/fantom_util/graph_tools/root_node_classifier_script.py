import numpy as np

from collections import Counter
from sqlalchemy.orm import joinedload

from fantom_util.feature_extraction import feature_extractor
from fantom_util import file_io_util
from fantom_util.db_util import connect_db

from fantom_util.misc import normalize_text
from fantom_util.models.rnc_mlp_model import RootNodeClassifierMLP
from fantom_util.models.rnc_rnn_model import RootNodeClassifierRNN

from fantom_util.database import db_session
from fantom_util.database.models import Node, NodeUtterance, Utterance


def get_child_count(node_id):
    return len(db_session.query(Node).filter(Node.parent_id == node_id).all())


def count_utterances(node, is_root, is_system_utt):
    # Loop through nodes, recursive call if given node has children
    utterance_data = {}

    if not is_system_utt and [
        normalize_text(utterance.utterance_text) for utterance in node.utterances
    ]:
        utterance_data = {
            node.id: {
                "texts": [
                    normalize_text(utterance.utterance_text)
                    for utterance in node.utterances
                ],
                "is_root": float(is_root),
            }
        }
        try:
            utterance_data[node.id]["rnc_mlps"] = [
                rnc_mlp.predict_string(utt) for utt in utterance_data[node.id]["texts"]
            ]
            utterance_data[node.id]["rnc_rnns"] = [
                rnc_rnn.predict_string(utt) for utt in utterance_data[node.id]["texts"]
            ]
            utterance_data[node.id]["rnc_mean"] = sum(
                utterance_data[node.id]["rnc_mlps"]
                + utterance_data[node.id]["rnc_rnns"]
            ) / float(2 * len(utterance_data[node.id]["texts"]))
            print(
                utterance_data[node.id]["is_root"],
                round(utterance_data[node.id]["rnc_mean"], 2),
                utterance_data[node.id]["texts"][0],
            )
        except:
            pass

    # for child in node.children:
    #    utterance_data.update(count_utterances(child, False, not is_system_utt))
    return utterance_data


def read_utterances_from_new_db():
    root_nodes = (
        db_session.query(Node)
        .options(joinedload(Node.children), joinedload(Node.utterances))
        .filter(Node.parent_id.is_(None), Node.visited_count < 3)
        .all()
    )
    global rnc_mlp
    global rnc_rnn
    rnc_mlp = RootNodeClassifierMLP()
    rnc_rnn = RootNodeClassifierRNN()
    utterances = {}
    for root_node in root_nodes:
        utterances.update(count_utterances(root_node, True, False))
    return utterances, len(utterances)


def upload_data(utterances, number_of_utterances):
    vocab_data = {
        "utterance_data": utterances,
        "number_of_utterances": number_of_utterances,
    }
    file_io_util.pickle_to_bucket(
        vocab_data, "SOME_AWS_BUCKET", "vocab_data_for_root_node_classifier"
    )


def download_data():
    vocab_data = file_io_util.unpickle_from_bucket(
        "SOME_AWS_BUCKET", "vocab_data_for_root_node_classifier"
    )
    return vocab_data["utterance_data"], vocab_data["number_of_utterances"]


def filter_probable_root_nodes(utterances, threshold, verbose=False):
    filtered_utterances = {}
    for node_id in utterances:
        try:
            if (
                utterances[node_id]["rnc_mean"] > threshold
                and not utterances[node_id]["is_root"]
            ):
                filtered_utterances[node_id] = utterances[node_id]
                if verbose:
                    print(
                        utterances[node_id]["is_root"],
                        round(utterances[node_id]["rnc_mean"], 1),
                        node_id,
                        utterances[node_id]["texts"][0],
                    )
        except:
            pass
    return filtered_utterances


def filter_improbable_root_nodes(utterances, threshold, verbose=False):
    filtered_utterances = {}
    for node_id in utterances:
        try:
            if (
                utterances[node_id]["rnc_mean"] < threshold
                and utterances[node_id]["is_root"]
            ):
                filtered_utterances[node_id] = utterances[node_id]
                if verbose:
                    print(
                        utterances[node_id]["is_root"],
                        round(utterances[node_id]["rnc_mean"], 1),
                        node_id,
                        utterances[node_id]["texts"][0],
                    )
        except:
            pass
    return filtered_utterances


def main():
    utterances, number_of_utterances = read_utterances_from_new_db()
    print("test")
    upload_data(utterances, number_of_utterances)
    utterances, number_of_utterances = download_data()

    improbable_rootnodes = filter_improbable_root_nodes(utterances, 0.1, verbose=True)


if __name__ == "__main__":
    main()
