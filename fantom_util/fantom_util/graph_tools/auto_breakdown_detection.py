import numpy as np

from collections import Counter
from sqlalchemy.orm import joinedload

from fantom_util import file_io_util
from fantom_util.db_util import connect_db

from fantom_util.feature_extraction import feature_extractor
from fantom_util.feature_extraction import specifications as sp

from fantom_util.misc import gen_feature_dict
from fantom_util.misc import normalize_text

from fantom_util.database import db_session
from fantom_util.database.models import Node, NodeUtterance, Utterance


def get_child_count(node_id):
    return len(db_session.query(Node).filter(Node.parent_id == node_id).all())


def extract_topic(utt_text):
    try:
        return fe({"text": utt_text})["topic"]
    except:
        return None


def extract_sentiment(utt_text):
    try:
        return fe({"text": utt_text})["sentiment"]
    except:
        return None


def get_most_frequent(a_list):
    # Gets most frequent element in a list
    counter = {}
    for elem in a_list:
        try:
            counter[elem] += 1
        except:
            counter[elem] = 1
    best_count = 0
    best_elem = None
    for elem in counter:
        if counter[elem] > best_count:
            best_count = counter[elem]
            best_elem = elem
    return best_elem


def contains_negative_words(utt_text):
    return any(
        word in utt_text for word in ["already", "boring", "sad", "stop", "stupid"]
    )


def count_utterances(node, is_root, is_system_utt, parent_id):
    # Loop through nodes, recursive call if given node has children
    utterance_data = {}
    print(node.id)
    utterance_data[node.id] = {}
    utterance_data[node.id]["is_root"] = is_root
    utterance_data[node.id]["is_system_utt"] = is_system_utt
    utterance_data[node.id]["parent"] = parent_id
    utterance_data[node.id]["texts"] = [
        normalize_text(utterance.utterance_text) for utterance in node.utterances
    ]
    utterance_data[node.id]["topics"] = [
        extract_topic(utt_text) for utt_text in utterance_data[node.id]["texts"]
    ]
    utterance_data[node.id]["sentiments"] = [
        extract_sentiment(utt_text) for utt_text in utterance_data[node.id]["texts"]
    ]
    utterance_data[node.id]["topic"] = get_most_frequent(
        utterance_data[node.id]["topics"]
    )
    utterance_data[node.id]["children"] = [child.id for child in node.children]

    for child in node.children:
        utterance_data.update(
            count_utterances(child, False, not is_system_utt, node.id)
        )
    return utterance_data


def locate_breakdowns():
    global problem_children
    problem_children = []
    for node_id in utterance_data:
        # print(utterance_data[node_id])
        if utterance_data[node_id]["is_root"]:
            # problem_children.append(recursive_breakdown_search(node_id))
            recursive_breakdown_search(node_id)


def is_breakdown(node_id):
    if not utterance_data[node_id]["children"]:
        return False
    if utterance_data[node_id]["parent"]:
        topicmatch_parent = (
            utterance_data[node_id]["topic"]
            == utterance_data[utterance_data[node_id]["parent"]]["topic"]
        )
    topicmatch_children = any(
        [
            (utterance_data[node_id]["topic"] == utterance_data[child_id])
            for child_id in utterance_data[node_id]["children"]
        ]
    )
    neg_sentiments = []
    for child_id in utterance_data[node_id]["children"]:
        neg_sentiments_of_child = [
            float(sentiment["neg"])
            for sentiment in utterance_data[child_id]["sentiments"]
        ]
        try:
            neg_sentiment_of_child = sum(neg_sentiments_of_child) / float(
                len(neg_sentiments_of_child)
            )
            neg_sentiments.append(neg_sentiment_of_child)
        except:
            pass
    neg_child_sent = any(
        contains_negative_words(child_utt_text)
        for child_utt_text in utterance_data[child_id]["texts"]
    )
    avg_neg_sentiment = sum(neg_sentiments) / float(max(1, len(neg_sentiments)))
    # return utterance_data[node_id]['is_system_utt'] or (not topicmatch_children) or (not topicmatch_parent) or (avg_neg_sentiment > 0.5) or neg_child_sent
    return utterance_data[node_id]["is_system_utt"] and neg_child_sent


def recursive_breakdown_search(node_id):
    for child_id in utterance_data[node_id]["children"]:
        # if utterance_data[child_id]['topic'] != utterance_data[node_id]['topic']:
        if is_breakdown(node_id):
            try:
                if utterance_data[node_id]["parent"]:
                    print(
                        "parent: "
                        + utterance_data[utterance_data[node_id]["parent"]]["texts"][0]
                    )
                print("node:   " + utterance_data[node_id]["texts"][0])
                print("child:  " + utterance_data[child_id]["texts"][0])
                print()
                print()
                # problem_children.append(child_id)
            except:
                pass

        recursive_breakdown_search(child_id)


def read_utterances_from_new_db():
    root_nodes = (
        db_session.query(Node)
        .options(joinedload(Node.children), joinedload(Node.utterances))
        .filter(Node.parent_id.is_(None))
        .all()
    )
    global features
    global fe
    features = gen_feature_dict(sp.TOPIC, sp.SENTIMENT)
    fe = feature_extractor.FeatureExtractor(features)
    utterance_data = {}
    for root_node in root_nodes:
        utterance_data.update(count_utterances(root_node, True, False, None))
    return utterance_data, len(utterance_data)


def upload_data():
    vocab_data = {
        "utterance_data": utterance_data,
        "number_of_utterances": number_of_utterances,
    }
    file_io_util.pickle_to_bucket(
        vocab_data, "SOME_AWS_BUCKET", "vocab_data_for_auto_breakdown_detection"
    )


def download_data():
    vocab_data = file_io_util.unpickle_from_bucket(
        "SOME_AWS_BUCKET", "vocab_data_for_auto_breakdown_detection"
    )
    return vocab_data["utterance_data"], vocab_data["number_of_utterances"]


def get_breakdowns(utterance_data):
    for node_id in utterance_data:
        if not utterance_data[node_id]["stays_on_topic"]:
            print(
                node_id,
                utterance_data[node_id]["topic"],
                utterance_data[node_id]["texts"][0],
            )
            print()
            print()


# utterance_data, number_of_utterances = read_utterances_from_new_db()
# upload_data()
utterance_data, number_of_utterances = download_data()
locate_breakdowns()
