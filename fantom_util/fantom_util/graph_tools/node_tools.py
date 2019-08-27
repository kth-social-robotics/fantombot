from fantom_util.database import db_session
from fantom_util.database.models import (
    Node,
    Utterance,
    NodeUtterance,
    JobNodeUtterance,
    NodeUtteranceWorkerJob,
    NodeUtteranceStatus,
    Merging,
    RootNode,
    PotentialNodeMerge,
    LinkedNodes,
)
from fantom_util.graph_tools.misc import get_full_child_count
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


def create_new_node(
    utterances, source="manual", parent_id=None, commit=False, species=None
):
    if type(parent_id) == Node:
        parent = parent_id
    elif parent_id is not None:
        parent = db_session.query(Node).get(parent_id)
    else:
        parent = None
    node = Node(parent=parent, species=species)
    db_session.add(node)
    db_session.flush()
    node.path = (parent.path if parent else []) + [node.id]
    if type(utterances) == str:
        utterances = [utterances]
    for utterance in utterances:
        add_utterance_to_node(utterance, node, source)
    if commit:
        db_session.commit()
    return node


def add_utterance_to_node(utterance_text, node, source):
    if not isinstance(utterance_text, Utterance):
        utterance = (
            db_session.query(Utterance).filter_by(utterance_text=utterance_text).first()
        )

        if not utterance:
            utterance = Utterance(utterance_text=utterance_text)
            db_session.add(utterance)
            db_session.flush()
    else:
        utterance = utterance_text

    node.utterances.append(utterance)
    db_session.flush()

    node_utterance = (
        db_session.query(NodeUtterance)
        .filter_by(node_id=node.id)
        .filter_by(utterance_id=utterance.id)
        .first()
    )

    node_utterance.source = source
    db_session.flush()
    return node_utterance


def linked_nodes(linked_to_node_id, linked_from_node_id):
    linked_to_node = db_session.query(Node).get(linked_to_node_id)
    linked_from_node = db_session.query(Node).get(linked_from_node_id)
    link = (
        db_session.query(LinkedNodes)
        .filter(
            LinkedNodes.linked_to_node_id == linked_to_node.id,
            LinkedNodes.linked_from_node_id == linked_from_node.id,
        )
        .first()
    )
    if link:
        return
    if linked_to_node and linked_from_node:
        db_session.add(
            LinkedNodes(
                linked_to_node_id=linked_to_node_id,
                linked_from_node_id=linked_from_node_id,
            )
        )
    db_session.commit()


def merge_nodes(left_node_id, right_node_id, merged=True):
    if merged:
        left_node = db_session.query(Node).get(left_node_id)
        right_node = db_session.query(Node).get(right_node_id)

        merge_1 = (
            db_session.query(Merging)
            .filter(
                Merging.left_node_id == left_node.id,
                Merging.right_node_id == right_node.id,
            )
            .first()
        )
        merge_2 = (
            db_session.query(Merging)
            .filter(
                Merging.left_node_id == right_node.id,
                Merging.right_node_id == left_node.id,
            )
            .first()
        )

        if merge_1 or merge_2:  # or left_node.id == right_node.id:
            return

        for node_utterance in right_node.node_utterances[:]:
            logger.debug(
                "node has utterance %s %s",
                node_utterance.id,
                node_utterance.utterance.utterance_text,
            )
            node_utterance.node = left_node
            node_utterance.node_id = left_node_id
            db_session.add(node_utterance)

            db_session.add(
                NodeUtteranceStatus(
                    node_utterance_id=node_utterance.id, status="merged"
                )
            )

        logger.debug("(before) left node children: %s", left_node.children)
        logger.debug("(before) right node children: %s", right_node.children)

        for child in right_node.children[:]:
            logger.debug("found child %s", child.id)
            set_parent(child.id, left_node.id)

        logger.debug("left node children: %s", left_node.children)
        logger.debug("right node children: %s", right_node.children)

        left_node.visited_count += right_node.visited_count
        db_session.commit()

        the_right_node_id = right_node.id
        inactivate_node(right_node.id)
        db_session.commit()
        db_session.add(
            Merging(
                left_node_id=left_node_id,
                right_node_id=the_right_node_id,
                merged=merged,
            )
        )
    else:
        db_session.add(
            Merging(
                left_node_id=left_node_id, right_node_id=right_node_id, merged=merged
            )
        )
        db_session.query(PotentialNodeMerge).filter(
            (PotentialNodeMerge.left_node_id == right_node_id)
            | (PotentialNodeMerge.right_node_id == right_node_id)
        ).delete()
    db_session.commit()


def split_nodes(node_id):
    node = db_session.query(Node).get(node_id)

    print(
        "which utterance for this node would you like to split (currently only one at a time) (enter to quit)"
    )
    split_utterances = {}
    for i, node_utterance in enumerate(node.node_utterances):
        split_utterances[i] = node_utterance
        print(f"({i}) {node_utterance.utterance.utterance_text}")
    print("")
    print("----- CHILDREN -----")
    for child in node.children:
        print("*", ", ".join([x.utterance_text for x in child.utterances]))
    print("-----")
    print("")
    utterance_to_split = input(">")
    if not utterance_to_split:
        return None
    split_node_utterance = split_utterances[int(utterance_to_split)]

    parent = node.parent

    new_node = create_new_node([], parent_id=parent, source="")
    split_node_utterance.node = new_node
    db_session.add(split_node_utterance)
    db_session.add(node)

    print("new node with utterance", [x.utterance_text for x in new_node.utterances])

    print(
        "Which children do you want to bring over to the new node (press enter for none, use comma for multiple)"
    )
    move_kids = {}
    for i, child in enumerate(node.children):
        move_kids[i] = child
        kids = ", ".join([x.utterance_text for x in child.utterances])
        print(f"({i}) {kids}")
    print("")

    kids_to_move = input(">").replace(" ", "")
    if kids_to_move:
        splited_kids = [int(x) for x in kids_to_move.split(",")]
        for kid in splited_kids:
            move_kids[kid].parent = new_node
            db_session.add(move_kids[kid])
            print(
                "adding", move_kids[kid].id, "to", new_node.id, move_kids[kid].parent.id
            )
    print("done")
    # db_session.rollback()
    db_session.commit()


def set_parent(node_id, parent_node_id=None, commit=False):
    node = db_session.query(Node).get(node_id)
    if not node:
        raise Exception("Could not find node")
    if parent_node_id:
        parent_node = db_session.query(Node).get(parent_node_id)
    else:
        parent_node = None

    old_parent_id = None
    if node.parent:
        old_parent_id = node.parent.id

    node.parent = parent_node
    node.path = node.recalculate_path()

    def update_children(child_node):
        db_session.add(child_node)
        child_node.path = child_node.recalculate_path()
        for child in child_node.children[:]:
            logger.debug("found child %s", child.id)
            logger.debug("parent has children %s", child_node.children)
            update_children(child)

    if old_parent_id and node.children:
        update_children(node)

    if commit:
        db_session.commit()
        logger.info("committing!")


def list_productive_parents():
    nodes = (
        db_session.query(Node)
        .filter(Node.active == True)
        .order_by(Node.child_count.desc())
        .limit(20)
        .all()
    )
    for node in nodes:
        size, depth = get_full_child_count(node)
        print(
            node.child_count,
            (size - 1),
            (depth - 1),
            " - ",
            node.id,
            ", ".join([x.utterance_text for x in node.utterances]),
        )


def delete_node(node_id):
    node = db_session.query(Node).get(node_id)
    for child in node.children:
        delete_node(child.id)
    for node_utterance in node.node_utterances:
        db_session.query(JobNodeUtterance).filter(
            JobNodeUtterance.node_utterance_id == node_utterance.id
        ).delete()
        db_session.query(NodeUtteranceStatus).filter(
            NodeUtteranceStatus.node_utterance_id == node_utterance.id
        ).delete()
        db_session.query(NodeUtteranceStatus).filter(
            NodeUtteranceStatus.referenced_node_utterance_id == node_utterance.id
        ).delete()
        db_session.query(NodeUtteranceWorkerJob).filter(
            NodeUtteranceWorkerJob.node_utterance_id == node_utterance.id
        ).delete()
        db_session.flush()
        db_session.delete(node_utterance)
    db_session.commit()
    db_session.delete(node)
    db_session.commit()


def kill_children(node_id):
    node = db_session.query(Node).get(node_id)
    print("-----------------------")
    print("\n".join([x.utterance_text for x in node.utterances]))
    print("-----------------------")
    print("which children do you want to keep (comma separated)?")
    michael_jacksons_list = {}
    for i, child in enumerate(
        sorted(node.children, key=lambda x: x.child_count, reverse=True)
    ):
        size, depth = get_full_child_count(child)
        print(
            f"({i}) - {node.child_count} {(size - 1)} {(depth - 1)}",
            ", ".join([x.utterance_text for x in child.utterances]),
        )
        michael_jacksons_list[i] = child
    user_input = input(">").replace(" ", "")
    if user_input:
        children = [int(x) for x in user_input.split(",")]
    else:
        return None

    for i, child in michael_jacksons_list.items():
        if i not in children:
            inactivate_node(child.id)


def inactivate_node(node_id):
    node = db_session.query(Node).get(node_id)
    node.active = False
    nodes = db_session.query(Node).filter(Node._path.descendant_of(node._path)).all()
    for node in nodes:
        node.active = False
    db_session.query(PotentialNodeMerge).filter(
        (PotentialNodeMerge.left_node_id == node_id)
        | (PotentialNodeMerge.right_node_id == node_id)
    ).delete()
    db_session.commit()


def activate_node(node_id):
    node = db_session.query(Node).get(node_id)
    node.active = True
    nodes = db_session.query(Node).filter(Node._path.descendant_of(node._path)).all()
    for node in nodes:
        node.active = True
    db_session.commit()


def classify_root_nodes():
    from fantom_util.models.rnc_mlp_model import RootNodeClassifierMLP

    nodes = (
        db_session.query(Node)
        .outerjoin(RootNode, RootNode.node_id == Node.id)
        .filter(Node.active.is_(True), Node.parent_id.is_(None), RootNode.id.is_(None))
        .order_by(Node.visited_count.desc())
        .all()
    )

    rnc_mlp = RootNodeClassifierMLP()
    for node in nodes:
        print("+----------------------+")
        utterances = [x.utterance_text for x in node.utterances]
        score_results = rnc_mlp.predict_list(utterances)
        for utterance, score in zip(utterances, score_results):
            print(f"{utterance}: {score[0]}")
        print("\navg:", (sum(score_results) / len(score_results))[0], "\n")

        user_input = input("Root node? Y/n/q ")
        if user_input.lower() == "q":
            exit()
        elif user_input.lower() == "n":
            node.active = False
            for utterance in utterances:
                db_session.add(
                    RootNode(node_id=node.id, utterance=utterance, is_root_node=False)
                )
        elif user_input == "" or user_input.lower() == "y":
            for utterance in utterances:
                db_session.add(
                    RootNode(node_id=node.id, utterance=utterance, is_root_node=True)
                )
        db_session.commit()


def merge_by_score():
    nodes = (
        db_session.query(
            PotentialNodeMerge.left_node_id,
            PotentialNodeMerge.right_node_id,
            PotentialNodeMerge.score,
            Merging,
        )
        .outerjoin(
            Merging,
            (
                (PotentialNodeMerge.left_node_id == Merging.left_node_id)
                & (PotentialNodeMerge.right_node_id == Merging.right_node_id)
                | (PotentialNodeMerge.left_node_id == Merging.right_node_id)
                & (PotentialNodeMerge.right_node_id == Merging.left_node_id)
            ),
        )
        .filter(Merging.id.is_(None))
        .order_by(PotentialNodeMerge.score.desc())
        .all()
    )

    used_ids = []
    merged_right_nodes = []

    for left_node_id, right_node_id, score, _ in nodes:
        if (
            f"{left_node_id}-{right_node_id}" not in used_ids
            and left_node_id not in merged_right_nodes
            and right_node_id not in merged_right_nodes
        ):
            used_ids.append(f"{left_node_id}-{right_node_id}")
            used_ids.append(f"{right_node_id}-{left_node_id}")
            print("+------------------+")
            left_node = db_session.query(Node).get(left_node_id)
            right_node = db_session.query(Node).get(right_node_id)
            if (
                left_node.active
                and right_node.active
                and left_node.utterances
                and right_node.utterances
            ):
                print(left_node_id, [x.utterance_text for x in left_node.utterances])
                print("---------------- VS ----------------")
                print(right_node_id, [x.utterance_text for x in right_node.utterances])

                print("\nscore", score, "\n")

                user_input = input("Merge? Y/n/q ")
                if user_input.lower() == "q":
                    exit()
                elif user_input.lower() == "n":
                    merge_nodes(left_node_id, right_node_id, merged=False)
                    print("nope!")
                elif user_input == "" or user_input.lower() == "y":
                    if right_node.child_count > left_node.child_count:
                        print(right_node.id, "<-", left_node.id)
                        merge_nodes(right_node.id, left_node.id, merged=True)
                        merged_right_nodes.append(left_node.id)
                    else:
                        print(left_node.id, "<-", right_node.id)
                        merge_nodes(left_node.id, right_node.id, merged=True)
                        merged_right_nodes.append(right_node.id)

                db_session.commit()


def incoherent_nodes():
    node_utterance_ids = (
        db_session.query(
            NodeUtteranceStatus.node_utterance_id,
            func.count(NodeUtteranceStatus.node_utterance_id),
        )
        .filter(
            NodeUtteranceStatus.status == "incoherent",
            NodeUtteranceStatus.handled.is_(False),
        )
        .group_by(NodeUtteranceStatus.node_utterance_id)
        .order_by(func.count(NodeUtteranceStatus.node_utterance_id).desc())
        .all()
    )
    for node_utterance_id, count in node_utterance_ids:
        node_utterance = db_session.query(NodeUtterance).get(node_utterance_id)
        history = (
            db_session.query(Node)
            .filter(Node.id.in_(node_utterance.node.path))
            .order_by(Node.path_length.asc())
            .all()
        )
        print("+----------------------------------+")
        print("node utterance id:", node_utterance_id)
        print("node id:", node_utterance.node.id)
        print("count:", count)
        print("\n")

        for h in history[:-1]:
            print([x.utterance_text for x in h.utterances])
        print(node_utterance.utterance.utterance_text)
        print("\n")
        user_input = input("Inactivate? Y/n/q ")
        if user_input.lower() == "q":
            exit()
        elif user_input == "" or user_input.lower() == "y":
            inactivate_node(node_utterance.node.id)

        db_session.query(NodeUtteranceStatus).filter(
            NodeUtteranceStatus.node_utterance_id == node_utterance_id,
            NodeUtteranceStatus.status == "incoherent",
        ).update({"handled": True})
        db_session.commit()

