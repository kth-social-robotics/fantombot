import math
import operator
import random
from math import floor
from operator import itemgetter

from fantom_util.constants import EXCLUDED_UTTERANCES
from fantom_util.database import db_session
from fantom_util.database.models import Utterance, Conversation, Node
from fantom_util.misc import normalize_text
from sqlalchemy import or_, func
from collections import defaultdict
import re

from sqlalchemy.orm import joinedload
from tqdm import tqdm


def fix_utterances_starting_with_alexa():
    utterances = db_session.query(Utterance)\
        .filter(
            Utterance.node_utterances.any(),
            or_(Utterance.utterance_text.like('alexa %'),
                Utterance.utterance_text.like('amazon %'),
                Utterance.utterance_text.like('echo %'),
                Utterance.utterance_text.like('computer %')
            )
    ).all()

    for utterance in utterances:
        nul = len(utterance.node_utterances)

        alternative_utterance = db_session.query(Utterance).filter(Utterance.utterance_text == normalize_text(utterance.utterance_text)).first()
        if alternative_utterance:
            for node_utterance in utterance.node_utterances:
                print('==', node_utterance.id)
                node_utterance.utterance = alternative_utterance
            print(utterance.utterance_text, '->', alternative_utterance.utterance_text, f'({nul})', utterance.id, alternative_utterance.id)
        else:
            print(normalize_text(utterance.utterance_text), utterance.utterance_text, 'HAS NO', f'({nul})')
    db_session.commit()


def test_profanity_filter():
    bad_utterances = []
    good_utterances = []

    ignore = ['test', 'of', 'profanity']
    safe_list = ['test', 'of', 'safe', 'words']

    conversations = db_session.query(Conversation.user_utterance, Conversation.candidates).order_by(Conversation.interaction_timestamp.desc()).all()
    for user_utterance, candidates in conversations:
        match = re.search(r'SAFETYFILTERBOT__\+__(.+?)(?=,"?(GRAPHSEARCH__\+__|EVIBOT__\+__|TOPICCHANGER__\+__))', candidates)
        if match and user_utterance:
            text = match.group(1)
            if text != '__EMPTY__' or user_utterance.startswith('alexa play ') or user_utterance.startswith('play ') or user_utterance in ignore:
                bad_utterances.append(user_utterance)
            elif user_utterance not in ignore:
                good_utterances.append(user_utterance)

    bad_count = 0
    b_list = []
    for b in bad_utterances:
        text = normalize_text(b)
        if text not in safe_list:
            if re.search(EXCLUDED_UTTERANCES, str(text)):
                bad_count += 1
            elif text not in safe_list:
                b_list.append(text)

    good_count = 0
    g_list = []

    for g in good_utterances:
        text = normalize_text(g)
        if text not in ignore:
            if not re.search(EXCLUDED_UTTERANCES, str(text)):
                good_count += 1
            else:
                g_list.append(text)
                print('____', text)

    appearances = defaultdict(int)

    for curr in b_list:
        appearances[curr] += 1

    print(b_list)
    print(g_list)
    for d, v in appearances.items():
        if v > 10:
            print('+', d, v)
    print(len(b_list), len(g_list))
    print(((bad_count/(len(b_list)+bad_count)) + (good_count/(len(g_list)+good_count)))/2)


def remove_profane_utterances():
    utterances = db_session.query(Utterance).all()
    for utterance in tqdm(utterances):
        text = normalize_text(utterance.utterance_text)
        if text and re.search(EXCLUDED_UTTERANCES, text) and utterance.node_utterances:
            node_ids = [x.node.id for x in utterance.node_utterances if x.node.is_user and x.node.active]
            if node_ids:
                print(text, node_ids)


def find_duplicate_utterances():
    duplicate_utterances = db_session.query(Utterance.utterance_text).group_by(Utterance.utterance_text).having(func.count(Utterance.utterance_text) > 1).all()
    for utterance_text, in duplicate_utterances:
        utterances = db_session.query(Utterance).filter(Utterance.utterance_text == utterance_text).all()
        print(utterance_text)
        print([(x.id, len(x.node_utterances)) for x in utterances])
        nu_count = 0
        candidate_utterance = utterances[0]
        for utterance in utterances:
            if utterance.node_utterances:
                candidate_utterance = utterance
                nu_count += 1
        if nu_count == 0 or nu_count == 1:
            print('deleting..')
            for utterance in utterances:
                if utterance.id != candidate_utterance.id:
                    print('removing..', utterance.id)
                    db_session.delete(utterance)
        print('-------------------')
    db_session.commit()


def reduce_ratio(load_list, total_num, min_num=1):
    """
    Returns the distribution of `total_num` in the ratio of `load_list` in the best possible way
    `min_num` gives the minimum per entry
    >>> reduce_ratio([5, 10, 15], 12)
    [2, 4, 6]
    >>> reduce_ratio([7, 13, 30], 6, 0)
    [1, 2, 3]
    >>> reduce_ratio([7, 13, 50], 6)
    [1, 1, 4]
    >>> reduce_ratio([7, 13, 50], 100, 15)
    [15, 18, 67]
    >>> reduce_ratio([7, 13, 50], 100)
    [10, 19, 71]
    """
    if not load_list:
        raise ValueError('Cannot distribute over an empty container')
    if any(l <= 0 for l in load_list):
        raise ValueError('Load list must contain only stricly positive elements')
    num_loads = [[load, min_num] for load in load_list]
    yet_to_split = total_num - sum(num for _, num in num_loads)
    if yet_to_split < 0:
        raise ValueError('Could not satisfy min_num')
    for _ in range(yet_to_split):
        min_elem = min(num_loads, key=lambda load_count: (float(load_count[1])/load_count[0], load_count[0]))
        min_elem[1] += 1
    reduced_loads = list(map(itemgetter(1), num_loads))
    assert (sum(reduced_loads) == total_num)
    return reduced_loads


def _check_kids(nodes, level, expected_visited_count):
    visited_count = 0
    childless_visited_count = 0
    childless_nodes = []

    for node in nodes:
        if node.children:
            child_visit_score = _check_kids(node.children, level+str(node.id)+'.', node.visited_count or 1)
            visited_count += child_visit_score
            print(level + str(node.id), node.visited_count or 1, child_visit_score)
            node.visited_count = child_visit_score
        else:
            childless_visited_count += node.visited_count or 1
            childless_nodes.append(node)

    if childless_nodes:
        diff_visited_count = expected_visited_count - visited_count
        if diff_visited_count < len(childless_nodes):
            diff_visited_count = len(childless_nodes)

        childless_ratios = [float(node.visited_count or 1) / float(childless_visited_count) for node in childless_nodes]
        if childless_visited_count > expected_visited_count and nodes[0].is_user and childless_ratios:
            print(level, diff_visited_count, childless_visited_count, len(nodes))
            for node, vc in zip(nodes, reduce_ratio(childless_ratios, diff_visited_count)):
                print('----', node.id, node.visited_count, vc)
                node.visited_count = vc
                visited_count += node.visited_count
        else:
            visited_count += childless_visited_count

    return visited_count


def fix_visited_count():
    nodes = db_session.query(Node).options(joinedload(Node.children), joinedload(Node.utterances)).filter(Node.parent_id.is_(None)).all()
    #nodes = [db_session.query(Node).get(648610)]
    _check_kids(nodes, '', 0)
    db_session.commit()


def fix_root_visited_count():
    nodes = db_session.query(Node).options(joinedload(Node.children)).filter(Node.parent_id.is_(None)).all()
    for node in tqdm(nodes):
        node.visited_count = sum([child.visited_count for child in node.children]) or 1
        db_session.commit()

fix_root_visited_count()