from fantom_util.feature_extraction.feature_extractor import FeatureExtractor
from fantom_util.feature_extraction.specifications import *
from fantom_util import score_functions as sf
import numpy as np
import time
import math

from fantom_util.misc import gen_feature_dict


def test_scoring(list_of_nodes, scoring_function):
    print("starting")

    list_of_utts = []
    utt_to_node = []

    for i in range(len(list_of_nodes)):
        for utt in list_of_nodes[i]:
            list_of_utts.append(utt)
            utt_to_node.append(i)
    score_mat = np.zeros((len(list_of_utts), len(list_of_utts)))
    ground_truth = score_mat.copy()
    for i in range(len(list_of_utts)):
        for j in range(i):
            if utt_to_node[i] == utt_to_node[j]:
                ground_truth[i][j] = 1
                ground_truth[j][i] = 1
    print("features extracted")
    start_time = time.time()
    for i in range(len(list_of_utts)):
        for j in range(i):
            score_mat[i][j] = scoring_function(list_of_utts[i], list_of_utts[j])
            score_mat[j][i] = score_mat[i][j]
            if math.isnan(score_mat[i][j]):
                print(list_of_utts[i]["text"], "  ", list_of_utts[j]["text"])
    total_time = time.time() - start_time
    best_F1, best_threshold, best_precision, best_recall, best_median_F1 = find_thresholds(
        score_mat, ground_truth
    )
    result_dict = {
        "best_F1": best_F1,
        "best_threshold": best_threshold,
        "total_time": total_time,
        "best_precision": best_precision,
        "best_recall": best_recall,
        "best_median_F1": best_median_F1,
    }
    print(result_dict)
    return result_dict


def find_thresholds(score_mat, ground_truth):
    granularity = 500
    thresholds = [float(i) / granularity for i in range(granularity)]
    best_mean_F1 = 0.0
    best_mean_precision = 0.0
    best_mean_recall = 0.0
    best_median_F1 = 0.0
    best_median_precision = 0.0
    best_median_recall = 0.0
    best_mean_threshold = 0.0
    best_median_threshold = 0.0
    for threshold in thresholds:
        pred_mat = score_mat > threshold
        true_pos = np.sum(np.multiply(pred_mat, ground_truth), axis=0)
        false_pos = np.sum(pred_mat > ground_truth, axis=0)
        false_neg = np.sum(pred_mat < ground_truth, axis=0)
        precision = true_pos / np.maximum(1.0, true_pos + false_pos)
        recall = true_pos / np.maximum(1.0, true_pos + false_neg)
        curr_F1 = 2 * precision * recall / (precision + recall)
        curr_F1[np.isnan(curr_F1)] = 0.0
        curr_mean_F1 = np.mean(curr_F1)
        curr_median_F1 = np.median(curr_F1)
        if curr_mean_F1 > best_mean_F1:
            best_mean_F1 = curr_mean_F1
            best_mean_threshold = threshold
            best_mean_precision = np.mean(precision)
            best_mean_recall = np.mean(recall)
        if curr_median_F1 > best_median_F1:
            best_median_F1 = curr_median_F1
            best_median_threshold = threshold
            # best_median_precision = np.median(precision)
            # best_median_recall = np.median(recall)
        # print(best_mean_F1, best_median_F1)
    return (
        best_mean_F1,
        best_mean_threshold,
        best_mean_precision,
        best_mean_recall,
        best_median_F1,
    )


def generate_features(list_of_nodes, features=None):
    if not features:
        features = gen_feature_dict(
            WORD_EMBEDDINGS,
            WORD_CLASS_SCORE,
            WORD_CLASS_VECTORS,
            WORD_CLASSES,
            SENTIMENT,
            TOPIC,
            LDA,
        )
    fe = FeatureExtractor(features)
    list_of_dicts = []
    print("nodes to extract features from:", len(list_of_nodes))
    for i in range(len(list_of_nodes)):
        list_of_dicts.append([])
        for utt in list_of_nodes[i]:
            list_of_dicts[i].append(fe({"text": utt}))
        print(i)
    return list_of_dicts


def main():
    test_list = [["hi", "hello"], ["what", "what do you mean", "I don't understand"]]
    test_scoring(generate_features(test_list), sf.graph_search_score)


if __name__ == "__main__":
    main()
