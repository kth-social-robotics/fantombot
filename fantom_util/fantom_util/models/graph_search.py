import random
import numpy as np

from fantom_util.score_functions import graph_search_score
from fantom_util.constants import SCORE_THRES_LOW
from fantom_util.feature_extraction.named_entities import untagged_text
from fantom_util.misc import tag_matcher
import logging

logger = logging.getLogger(__name__)


def find_reply(model, user_utt, history, in_root_node, blocked_children):
    logger.info("graphsearch received the text: %s %s", user_utt["text"], in_root_node)
    return choose_best_reply(
        model,
        *find_best_match(model, user_utt, history, in_root_node, blocked_children)
    )


def find_best_match(model, user_utt, history, in_root_node, blocked_children):

    lookup_table = model["lookup_table"]
    node_utts = model["node_utts"]
    id_utt = model["id_utt"]

    matched_node = 0
    best_score = -1
    matched_utt = None
    match_candidates = []

    if history:
        blocked_children.insert(0, history)
        for key, value in model["linked_nodes"].items():
            if history == value:
                blocked_children.insert(0, key)

    for child_id in lookup_table[history]:
        children = list(set(lookup_table[child_id]) - set(blocked_children))

        if len(children) > 0:
            for utt_id in node_utts[child_id]:
                if history:
                    match_candidates.append(id_utt[utt_id]["text"])

                score = graph_search_score(user_utt, id_utt[utt_id])

                if score > best_score:
                    best_score = score
                    matched_node = child_id
                    matched_utt = id_utt[utt_id]["text"]

                    # if history:
                    candidates = model["lookup_table"][matched_node]
                    candidates = list(set(candidates) - set(blocked_children))
                    for node in candidates:
                        response_candidates = model["node_utts"][node]
                        for response in response_candidates:
                            utt = model["id_utt"][response]["text"]
                            if tag_matcher(utt):
                                try:
                                    untagged_text(
                                        utt,
                                        user_utt["named_entities"],
                                        model["named_entity_model"],
                                    )
                                except:
                                    blocked_children.insert(0, node)
                                    return find_best_match(
                                        model,
                                        user_utt,
                                        history,
                                        in_root_node,
                                        blocked_children,
                                    )
                    if score == 1:
                        # visited_user_nodes.append(matched_node)
                        logger.info(matched_node)

                        if not history:
                            if not in_root_node:
                                in_root_node = matched_node
                            elif in_root_node != matched_node:
                                in_root_node = matched_node

                        logger.info("set in_root_node to %s", in_root_node)

                        return (
                            user_utt,
                            matched_node,
                            best_score,
                            history,
                            match_candidates,
                            matched_utt,
                            in_root_node,
                            blocked_children,
                        )

    if isinstance(history, int) and best_score < SCORE_THRES_LOW:
        logger.info("Children high score before going to root nodes: %s", best_score)
        history = None
        return find_best_match(model, user_utt, history, in_root_node, blocked_children)

    if not history:
        if not in_root_node:
            in_root_node = matched_node
        elif in_root_node != matched_node:
            in_root_node = matched_node

    logger.info("set in_root_node to %s", in_root_node)

    logger.info(matched_node)
    return (
        user_utt,
        matched_node,
        best_score,
        history,
        match_candidates,
        matched_utt,
        in_root_node,
        blocked_children,
    )


def choose_best_reply(
    model,
    user_utt,
    matched_node,
    score,
    history,
    match_candidates,
    matched_utt,
    in_root_node,
    blocked_children,
):
    logger.info("in cbr matched node: %s", matched_node)

    candidates = model["lookup_table"][matched_node]

    candidates = list(set(candidates) - set(blocked_children))

    logger.info("in br candidates: %s", candidates)

    found_tag = False

    for candidate in candidates:
        response_candidates = model["node_utts"][candidate]
        for response in response_candidates:
            utt = model["id_utt"][response]["text"]
            if tag_matcher(utt):
                found_tag = True
                response_node = candidate

    if not found_tag:
        candidates_visits = [model["node_visit_counts"][key] for key in candidates]
        visit_counts = np.array(candidates_visits)
        response_node = np.random.choice(
            candidates, 1, p=visit_counts / np.sum(visit_counts)
        )
        response_node = int(response_node)

    response_candidates = model["node_utts"][response_node]
    response_utterance_id = random.choice(response_candidates)
    response = model["id_utt"][response_utterance_id]["text"]

    response, mentioned_named_entities = untagged_text(
        response, user_utt["named_entities"], model["named_entity_model"]
    )

    logger.info(
        "linking nodes : %s %s",
        response_node,
        model["linked_nodes"].get(response_node, response_node),
    )
    response_node = model["linked_nodes"].get(response_node, response_node)

    expected_next_user_nodes = model["lookup_table"][response_node]

    expected_next_user_utts = []
    for node in expected_next_user_nodes:
        for utt_id in model["node_utts"][node]:
            expected_next_user_utts.append(model["id_utt"][utt_id]["text"])

    return (
        response,
        response_node,  # This value is 'history' in the next turn
        response_candidates,
        matched_utt,
        matched_node,
        match_candidates,
        score,
        expected_next_user_nodes,
        expected_next_user_utts,
        in_root_node,
        blocked_children,
        response_utterance_id,
    )

