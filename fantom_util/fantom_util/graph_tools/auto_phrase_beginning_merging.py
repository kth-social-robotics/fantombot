import sys

from fantom_util.constants import FANTOM_WORKDIR
from fantom_util.database import db_session
from fantom_util.database.models import Node, Utterance
from fantom_util.graph_tools.node_tools import merge_nodes
from sqlalchemy.orm import joinedload
from fantom_util.misc import normalize_text
import glob


def get_child_count(node_id):
    return len(db_session.query(Node).filter(Node.parent_id == node_id).all())


def merge_synonyms(nodes, synonym_objects):
    # Loop through nodes, recursive call if given node has children
    dict_of_merge_nodes = {}
    var = 0
    for node in nodes:
        if node.children:
            merge_synonyms(node.children, synonym_objects)

        utterance_texts = [
            normalize_text(utterance.utterance_text) for utterance in node.utterances
        ]
        for phrase_beginning in [synonym.utterance_text for synonym in synonym_objects]:

            contains_starters = [
                phrase_beginning.lower() == utterance_text.lower()
                for utterance_text in [
                    utterance_texts[i][
                        0 : min(len(phrase_beginning), len(utterance_texts[i]))
                    ]
                    for i in range(len(utterance_texts))
                ]
            ]

            for i in range(len(contains_starters)):
                if contains_starters[i]:
                    ending = utterance_texts[i][
                        min(len(phrase_beginning), len(utterance_texts[i])) : len(
                            utterance_texts[i]
                        )
                    ].lower()
                    if ending in dict_of_merge_nodes:
                        if node not in dict_of_merge_nodes[ending]:
                            dict_of_merge_nodes[ending].append(node)
                    else:
                        dict_of_merge_nodes[ending] = [node]
    popped_nodes = []
    for key in dict_of_merge_nodes:
        nodes_to_merge = dict_of_merge_nodes[key]
        # If at least two childs contain synonyms, merge them
        if len(nodes_to_merge) > 1:

            # Sorting list by childcount, highest to the left
            nodes_to_merge = sorted(
                nodes_to_merge,
                key=lambda child: get_child_count(child.id),
                reverse=True,
            )

            # Merge first index with popped last until only one left
            while len(nodes_to_merge) > 1:
                pop_node = nodes_to_merge.pop()
                if pop_node not in popped_nodes:
                    merge_nodes(nodes_to_merge[0].id, pop_node.id)
                    print([utt.utterance_text for utt in nodes_to_merge[0].utterances])
                    print("---")
                    print([utt.utterance_text for utt in pop_node.utterances])
                    var += 1
                    print(var)
                    print()
                    print()

        ## Add synonym utterances to remaining/only node
        # if len(nodes_to_merge) == 1:
        #   remaining_node = nodes_to_merge[0]
        #   for synonym_object in synonym_objects:
        #       if synonym_object.utterance_text not in [utterance.utterance_text for utterance in remaining_node.utterances]:
        #           add_utterance_to_node(synonym_object, remaining_node, "synonym_population")
    print("merged nodes: ", var)


def get_synonym_objects(synonym_path):
    synonym_objects = []
    with open(synonym_path, "r") as f:
        for synonym in f.readlines():
            utterance = (
                db_session.query(Utterance)
                .filter_by(utterance_text=synonym.strip())
                .first()
            )
            if not utterance:
                utterance = Utterance(utterance_text=synonym.strip())
                db_session.add(utterance)
                db_session.flush()
            synonym_objects.append(utterance)
    return synonym_objects


def main(synonym_path):
    synonym_objects = get_synonym_objects(synonym_path)
    root_nodes = (
        db_session.query(Node)
        .options(joinedload(Node.children), joinedload(Node.utterances))
        .filter(Node.parent_id.is_(None))
        .all()
    )
    merge_synonyms(root_nodes, synonym_objects)
    db_session.commit()


def merge_multiple_phrase_beginning_lists():
    for f in glob.glob(f"{FANTOM_WORKDIR}/sleepwalker/phrase_beginnings/*.txt"):
        main(f)


if __name__ == "__main__":
    main(sys.argv[1])
