from fantom_util.database import db_session
from fantom_util.database.models import Node, Merging
from fantom_util.graph_tools.node_tools import merge_nodes
from collections import defaultdict
import progressbar


def exact_match():
    merges = db_session.query(Merging).all()
    used_nodes = []

    for merge in merges:
        used_nodes.append(f"{merge.left_node_id}--{merge.right_node_id}")

    nodes = (
        db_session.query(Node)
        .filter(Node.active == True)
        .order_by(Node.parent_id.desc())
        .all()
    )
    grouped_nodes = defaultdict(list)

    for node in nodes:
        grouped_nodes[node.parent_id].append(node)

    bar = progressbar.ProgressBar()
    for group, grouped_nodes in bar(grouped_nodes.items()):
        for i, left_node in enumerate(grouped_nodes):
            for j, right_node in enumerate(grouped_nodes):
                if (
                    i != j
                    and f"{left_node.id}--{right_node.id}" not in used_nodes
                    and f"{right_node.id}--{left_node.id}" not in used_nodes
                ):
                    used_nodes.append(f"{left_node.id}--{right_node.id}")
                    for left_utterance in left_node.utterances:
                        for right_utterance in right_node.utterances:
                            do_continue = True
                            if (
                                left_utterance.utterance_text == ""
                                or left_utterance.utterance_text == " "
                            ):
                                print(
                                    "removing empty utterance",
                                    left_utterance.utterance_text,
                                    left_utterance.id,
                                )
                                if left_node.children:
                                    raise Exception(
                                        "empty string has children. WAT?! :S"
                                    )
                                db_session.remove(left_utterance)
                                db_session.flush()
                                if not left_node.utterances:
                                    print("removing node", left_node.id)
                                    db_session.remove(left_node)
                                do_continue = False

                            if (
                                right_utterance.utterance_text == ""
                                or right_utterance.utterance_text == " "
                            ):
                                print(
                                    "removing empty utterance",
                                    right_utterance.utterance_text,
                                    right_utterance.id,
                                )
                                if right_node.children:
                                    raise Exception(
                                        "empty string has children. WAT?! :S"
                                    )
                                db_session.remove(right_utterance)
                                db_session.flush()
                                if not right_node.utterances:
                                    print("removing node", right_node.id)
                                    db_session.remove(right_node)
                                do_continue = False

                            if (
                                do_continue
                                and left_utterance.utterance_text.lower()
                                == right_utterance.utterance_text.lower()
                            ):
                                # print('merge', left_utterance.utterance_text, right_utterance.utterance_text)
                                merge_nodes(left_node.id, right_node.id, True)

    db_session.commit()
