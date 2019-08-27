import glob
import sys

from fantom_util.constants import FANTOM_WORKDIR
from fantom_util.database import db_session
from fantom_util.database.models import Node, Utterance
from fantom_util.graph_tools.node_tools import merge_nodes, add_utterance_to_node
from sqlalchemy.orm import joinedload


def get_child_count(node_id):
    return len(db_session.query(Node).filter(Node.parent_id == node_id).all())


def merge_synonyms(nodes, synonym_objects):
    # Loop through nodes, recursive call if given node has children
    nodes_to_merge = []
    for node in nodes:
        if node.children:
            merge_synonyms(node.children, synonym_objects)

        for utterance in node.utterances:
            if utterance.utterance_text in [
                synonym.utterance_text for synonym in synonym_objects
            ]:
                nodes_to_merge.append(node)
                break

    # If at least two childs contain synonyms, merge them
    if len(nodes_to_merge) > 1:

        # Sorting list by childcount, highest to the left
        nodes_to_merge = sorted(
            nodes_to_merge, key=lambda child: get_child_count(child.id), reverse=True
        )

        # Merge first index with popped last until only one left
        while len(nodes_to_merge) > 1:
            merge_nodes(nodes_to_merge[0].id, nodes_to_merge.pop().id)
            # print(nodes_to_merge[0], nodes_to_merge.pop())

    # Add synonym utterances to remaining/only node
    if len(nodes_to_merge) == 1:
        remaining_node = nodes_to_merge[0]
        for synonym_object in synonym_objects:
            if synonym_object.utterance_text not in [
                utterance.utterance_text for utterance in remaining_node.utterances
            ]:
                add_utterance_to_node(
                    synonym_object, remaining_node, "synonym_population"
                )


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


def merge_multiple_synonym_lists():
    for f in glob.glob(f"{FANTOM_WORKDIR}/sleepwalker/synonyms/*.txt"):
        main(f)


if __name__ == "__main__":
    main(sys.argv[1])
