"""Provide a similarity measure between utterance representations"""
import os

import numpy as np
import math


def graph_search_score(vec1, vec2, test_mode=False):
    """Calculates the similarity score between two utterances"""
    try:
        if not vec1["word_embeddings"] or not vec2["word_embeddings"]:
            return 0.0
    except:
        pass

    if vec1.get("tagged_text"):
        if vec1["tagged_text"].lower() == vec2["text"].lower():
            return 1
        else:
            return global_score_both(vec1, vec2)
    else:
        if vec1["text"].lower() == vec2["text"].lower():
            return 1
        else:
            return global_score_both(vec1, vec2)


def _cosine_sim_norm(data1, data2):
    return np.dot(data1, data2)


def _normalize(v):
    norm = np.linalg.norm(v)
    return v if norm == 0 else v / norm


def global_score_only_weighted(vec1, vec2):
    scores = {}
    scores["topic"] = topic_score(vec1, vec2)
    scores["sentiment"] = sentiment_score(vec1, vec2)
    # scores['word_class_vectors'] = word_classes_score(vec1, vec2)
    scores["weighted_score"] = weighted_score(vec1, vec2)
    total_score = 1.0
    for score_type in scores:
        total_score *= scores[score_type]
    return total_score


def global_score_only_word_class(vec1, vec2):
    scores = {}

    scores["topic"] = topic_score(vec1, vec2)
    scores["sentiment"] = sentiment_score(vec1, vec2)

    scores["word_class_vectors"] = word_classes_score1(vec1, vec2)
    # scores['weighted_score'] = weighted_score(vec1, vec2)

    total_score = 1.0
    for score_type in scores:
        total_score *= scores[score_type]
    return total_score


def global_score_both(vec1, vec2):
    scores = {}

    scores["topic"] = topic_score(vec1, vec2)
    scores["sentiment"] = sentiment_score(vec1, vec2)

    scores["maxer"] = max(
        word_classes_score1(vec1, vec2), weighted_score(vec1, vec2) ** 2
    )
    total_score = 1.0
    for score_type in scores:
        total_score *= scores[score_type]
    return total_score


def global_score_both2(vec1, vec2):
    scores = {}

    scores["topic"] = topic_score(vec1, vec2)
    scores["sentiment"] = sentiment_score(vec1, vec2)

    scores["spec_avg"] = 1.0 - math.sqrt(
        max(1.0 - word_classes_score1(vec1, vec2), 0.0)
        * max(1.0 - weighted_score(vec1, vec2) ** 2, 0.0)
    )
    total_score = 1.0
    for score_type in scores:
        total_score *= scores[score_type]
    return total_score


def global_score_both3(vec1, vec2):
    scores = {}

    scores["topic"] = topic_score(vec1, vec2)
    scores["sentiment"] = sentiment_score(vec1, vec2)

    scores["spec_avg"] = 1.0 - math.sqrt(
        max(1.0 - word_classes_score1(vec1, vec2), 0.0)
        * max(1.0 - weighted_score(vec1, vec2) ** 3, 0.0)
    )
    total_score = 1.0
    for score_type in scores:
        total_score *= scores[score_type]
    return total_score


def global_score_both4(vec1, vec2):
    scores = {}

    scores["topic"] = topic_score(vec1, vec2)
    scores["sentiment"] = sentiment_score(vec1, vec2)

    scores["spec_avg"] = 1.0 - math.sqrt(
        max(1.0 - word_classes_score1(vec1, vec2), 0.0)
        * max(1.0 - weighted_score(vec1, vec2), 0.0)
    )
    total_score = 1.0
    for score_type in scores:
        total_score *= scores[score_type]
    return total_score


def global_score_both5(vec1, vec2):
    scores = {}

    scores["topic"] = topic_score(vec1, vec2)
    scores["sentiment"] = sentiment_score(vec1, vec2)

    scores["spec_avg"] = 1.0 - math.sqrt(
        max(1.0 - word_classes_score1(vec1, vec2) ** 2, 0.0)
        * max(1.0 - weighted_score(vec1, vec2), 0.0)
    )
    total_score = 1.0
    for score_type in scores:
        total_score *= scores[score_type]
    return total_score


def sentiment_score(vec1, vec2):
    try:
        compound_dist = abs(
            vec1["sentiment"]["compound"] - vec2["sentiment"]["compound"]
        )
        return max(0.8, 1.0 - compound_dist ** 4)
    except:
        return 0.98


def ner_score(vec1, vec2):
    lower = 0.94
    try:
        score = 1.0 if vec1["ner"]["text"] == vec2["ner"]["text"] else lower
    except:
        score = lower
    return score


def topic_score(vec1, vec2):
    try:
        if vec1["topic"] and vec2["topic"]:
            return 1.0 if vec1["topic"] == vec2["topic"] else 0.94
        else:
            return 0.98
    except:
        return 0.98


def word_classes_score(vec1, vec2):
    score = 0.0
    normalization = 0.0
    # threshold should be dependent on how many words we have
    lower_thres = 0.5

    word_class_weights = {
        "ADJ": 0.4,
        "ADP": 0.01,
        "ADV": 0.25,
        "AUX": 0.25,
        "CCONJ": 0.01,
        "DET": 0.01,
        "INTJ": 0.01,
        "NOUN": 3.0,
        "NUM": 0.01,
        "PART": 0.01,
        "PRON": 0.02,
        "PROPN": 0.3,
        "PUNCT": 0.01,
        "SCONJ": 0.01,
        "SYM": 0.01,
        "VERB": 0.5,
        "X": 0.3,
        "SPACE": 0.01,
        "TAG": 0.9,
    }

    word_class_scores = {}
    word_class_vec1 = vec1["word_class_vectors"]
    word_class_vec2 = vec2["word_class_vectors"]
    word_class_list1 = sorted(list(set(vec1["word_classes"])))
    word_class_list2 = sorted(list(set(vec2["word_classes"])))
    for i in range(len(word_class_list1)):
        for j in range(len(word_class_list2)):
            if word_class_list1[i] == word_class_list2[j]:
                cos_sim = _cosine_sim_norm(word_class_vec1[i], word_class_vec2[j])
                word_class_scores[word_class_list1[i]] = max(lower_thres, cos_sim)
                score += (
                    word_class_weights[word_class_list1[i]]
                    * word_class_scores[word_class_list1[i]]
                )
                normalization += word_class_weights[word_class_list1[i]]

    word_class_union = set(vec1["word_classes"]).union(set(vec2["word_classes"]))
    word_class_intersection = set(vec1["word_classes"]).intersection(
        set(vec2["word_classes"])
    )

    for word_class in list(word_class_union - word_class_intersection):
        word_class_scores[word_class] = lower_thres
        score += word_class_weights[word_class] * word_class_scores[word_class]
        normalization += word_class_weights[word_class]
    return score / normalization


def word_classes_score1(vec1, vec2):

    score = 0.0
    normalization = 0.0
    lower_thres = 0.65

    word_class_weights = {
        "ADJ": 0.4,
        "ADP": 0.01,
        "ADV": 0.25,
        "AUX": 0.25,
        "CCONJ": 0.01,
        "DET": 0.01,
        "INTJ": 0.01,
        "NOUN": 3.0,
        "NUM": 0.01,
        "PART": 0.01,
        "PRON": 0.02,
        "PROPN": 0.3,
        "PUNCT": 0.01,
        "SCONJ": 0.01,
        "SYM": 0.01,
        "VERB": 0.5,
        "X": 0.3,
        "SPACE": 0.01,
        "TAG": 0.9,
    }

    word_class_scores = {}
    word_class_vec1 = vec1["word_class_vectors"]
    word_class_vec2 = vec2["word_class_vectors"]
    word_class_list1 = sorted(list(set(vec1["word_classes"])))
    word_class_list2 = sorted(list(set(vec2["word_classes"])))
    for i in range(len(word_class_list1)):
        for j in range(len(word_class_list2)):
            if word_class_list1[i] == word_class_list2[j]:
                cos_sim = _cosine_sim_norm(word_class_vec1[i], word_class_vec2[j])
                word_class_scores[word_class_list1[i]] = max(lower_thres, cos_sim)
                score += (
                    word_class_weights[word_class_list1[i]]
                    * word_class_scores[word_class_list1[i]]
                )
                normalization += word_class_weights[word_class_list1[i]]

    word_class_union = set(vec1["word_classes"]).union(set(vec2["word_classes"]))
    word_class_intersection = set(vec1["word_classes"]).intersection(
        set(vec2["word_classes"])
    )

    for word_class in list(word_class_union - word_class_intersection):
        word_class_scores[word_class] = lower_thres
        score += word_class_weights[word_class] * word_class_scores[word_class]
        normalization += word_class_weights[word_class]
    return score / normalization


def _get_word_weights(vec1, vec2):
    weights1 = np.asarray(vec1["word_class_score"])
    weights2 = np.asarray(vec2["word_class_score"])
    return weights1, weights2


def _get_word_embeds(vec1, vec2):
    word_embeds1 = np.asarray(vec1["word_embeddings"])
    word_embeds2 = np.asarray(vec2["word_embeddings"])
    return word_embeds1, word_embeds2


def weighted_score(vec1, vec2):
    weights1, weights2 = _get_word_weights(vec1, vec2)
    word_embeds1, word_embeds2 = _get_word_embeds(vec1, vec2)

    mat1 = (word_embeds1.T * weights1).T
    mat2 = (word_embeds2.T * weights2).T

    mean1 = np.mean(mat1, axis=0)
    mean2 = np.mean(mat2, axis=0)

    mean1 = _normalize(mean1)
    mean2 = _normalize(mean2)

    return _cosine_sim_norm(mean1, mean2)


def average_word_embedding_score(vec1, vec2):
    weights1, weights2 = _get_word_weights(vec1, vec2)
    weights1 = np.ones(weights1.shape)
    weights2 = np.ones(weights2.shape)
    word_embeds1, word_embeds2 = _get_word_embeds(vec1, vec2)

    mat1 = (word_embeds1.T * weights1).T
    mat2 = (word_embeds2.T * weights2).T

    mean1 = np.mean(mat1, axis=0)
    mean2 = np.mean(mat2, axis=0)

    mean1 = _normalize(mean1)
    mean2 = _normalize(mean2)

    return _cosine_sim_norm(mean1, mean2)
