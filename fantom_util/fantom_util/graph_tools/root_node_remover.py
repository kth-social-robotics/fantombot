from sqlalchemy.orm import joinedload
from fantom_util.constants import FANTOM_WORKDIR
from fantom_util.database import db_session
from fantom_util.database.models import Node

from fantom_util.graph_tools.node_tools import delete_node


def add_utt_to_file(utt_text, node_id, file_name):
    with open(file_name, "a") as storage_file:
        storage_file.write(utt_text + " - " + str(node_id) + "\n")


def remove_questionable_root_nodes():
    file_name = (
        FANTOM_WORKDIR + "/fantom_util/fantom_util/graph_tools/removed_root_nodes.txt"
    )
    root_nodes = (
        db_session.query(Node)
        .options(joinedload(Node.children), joinedload(Node.utterances))
        .filter(
            Node.parent_id.is_(None),
            Node.visited_count == 1,
            Node.species.is_(None),
            Node.child_count == 0,
        )
        .all()
    )
    for node in root_nodes:
        for utterance in node.utterances:
            add_utt_to_file(utterance.utterance_text, node.id, file_name)
            print("Removing: ", utterance.utterance_text)

        # Make sure to empty file before doing this:
        delete_node(node.id)


def main():
    remove_questionable_root_nodes()


if __name__ == "__main__":
    main()
