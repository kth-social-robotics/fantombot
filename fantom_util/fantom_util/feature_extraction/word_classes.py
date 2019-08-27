import numpy as np
from fantom_util.constants import WORD_CLASS_WEIGHTS
from fantom_util.misc import unique
from fantom_util.score_functions import _normalize


def word_class_vectors(word_embeddings, word_classes):
    if not any([word_embeddings, word_classes]):
        return None
    unique_word_classes = unique(word_classes)
    output = []
    for word_class in unique_word_classes:
        word_vectors = []
        for index, value in enumerate(word_classes):
            if value == word_class:
                word_vectors.append(word_embeddings[index])
        cur_vec = np.mean(np.asarray(word_vectors), axis=0)
        cur_vec = cur_vec / np.linalg.norm(cur_vec)
        output.append(cur_vec)
    return output


def word_class_score(word_classes):
    if not word_classes:
        return None
    return [WORD_CLASS_WEIGHTS[word_class] for word_class in word_classes]


def weighted_average_word_embeddings(word_embeddings, word_class_score):
    weights = np.asarray(word_class_score)
    word_embeds = np.asarray(word_embeddings)
    mat = (word_embeds.T * weights).T
    mean = np.mean(mat, axis=0)
    mean = _normalize(mean)
    return mean
