from fantom_util.feature_extraction import feature_extractor
from fantom_util import file_io_util
from fantom_util.db_util import connect_db
import spacy
import sys
import numpy as np
from collections import Counter
from fantom_util.database import db_session
from fantom_util.database.models import Node, NodeUtterance, Utterance
from sqlalchemy.orm import joinedload
from fantom_util.misc import normalize_text


def get_child_count(node_id):
    return len(db_session.query(Node).filter(Node.parent_id == node_id).all())


def count_utterances(node):
    # Loop through nodes, recursive call if given node has children
    utterance_texts = [
        normalize_text(utterance.utterance_text) for utterance in node.utterances
    ]
    for child in node.children:
        utterance_texts += count_utterances(child)
    print(utterance_texts)
    return utterance_texts


def read_utterances_from_new_db():
    root_nodes = (
        db_session.query(Node)
        .options(joinedload(Node.children), joinedload(Node.utterances))
        .filter(Node.parent_id.is_(None))
        .all()
    )
    utterances = []
    for root_node in root_nodes:
        utterances += count_utterances(root_node)
    return utterances, len(utterances)


def read_utterances_from_alexaprize2017():
    inputWb = openpyxl.load_workbook("root_node_classifier_stuff//Root_nodes.xlsx")
    inputS = inputWb.active
    number_of_utterances = 320472
    utterances = []
    for row in range(number_of_utterances):
        utterances.append((inputS["A" + str(row + 1)].value).lower())
    return utterances, number_of_utterances


def count_word_occurences(utterances):
    word_freq_counter = Counter()
    number_of_words = 0
    for i in range(len(utterances)):
        for token in nlp(utterances[i]):
            word_freq_counter[token.orth_] += 1
            number_of_words += 1
    return word_freq_counter, number_of_words


utterances1, number_of_utterances1 = read_utterances_from_new_db()
# utterances1, number_of_utterances1 = read_utterances_from_db()
# utterances2, number_of_utterances2 = read_utterances_from_alexaprize2017()

# utterances = utterances1 + utterances2
# number_of_utterances = number_of_utterances1 + number_of_utterances2

utterances = utterances1
number_of_utterances = number_of_utterances1

nlp = spacy.load("en_core_web_lg")
word_freq_counter, number_of_words = count_word_occurences(utterances)
vocab_data = {
    "word_frequencies": word_freq_counter,
    "number_of_utterances": number_of_utterances,
}
file_io_util.pickle_to_bucket(vocab_data, "SOME_AWS_BUCKET", "vocab_data_for_tfidf")

for key in vocab_data:
    print(key)
    print(vocab_data[key])
print(number_of_words)
