from fantom_util.graph_tools.node_tools import create_new_node
from fantom_util.database import db_session
from fantom_util.database.models import Node, NodeUtterance, Utterance
import re


def create_expected_answer_children(expected_answers, parent):
    source = "expected_answer"

    for utterance in expected_answers:
        species = utterance  # species set to utterance for Y/N children
        create_new_node(utterance, parent, source, commit=False)
    print("done")


def expected_answers_nodes(expected_answers, parents):
    for parent in parents:
        create_expected_answer_children(expected_answers, parent)
    print("done")


def get_node_utterances(node_id):
    node_utterances = (
        db_session.query(NodeUtterance).filter(NodeUtterance.node_id == node_id).all()
    )
    for node_utterance in node_utterances:
        utterances = (
            db_session.query(Utterance)
            .filter(Utterance.id == node_utterance.utterance_id)
            .all()
        )
        for utterance in utterances:
            yield utterance.utterance_text


def add_yes_no_nodes():
    text_file = open("nodeIDs_final.txt", "r")
    node_ids = text_file.read().split("\n")[:-1]

    nodes = (
        db_session.query(Node)
        .filter(Node.is_user == False, Node.id.in_(map(int, node_ids)))
        .all()
    )

    # Filter out nodes that already have yes/no children
    nodes_add_yes = []
    nodes_add_no = []
    for node in nodes:
        add_yes, add_no = True, True
        yes_utterances, no_utterances = [], []
        children = db_session.query(Node).filter(Node.parent_id == node.id).all()
        for child in children:
            for utterance in get_node_utterances(child.id):
                if re.match(
                    r".*\b(ye(s\b|ah\b|a\b|p\b)|of course|I do\b|absolutely|definitely|ok\b|ok(ay|ey)\b|sounds (good|great)|fine|sure|why not|don't mind|let's do that).*",
                    utterance,
                ):
                    add_yes = False
                if re.match(
                    r".*\b(n(o\bo\b||ot\b|ope\b|a\b|ah\b)|sounds bad|I'm good).*",
                    utterance,
                ):
                    add_no = False
        if add_yes:
            nodes_add_yes.append(node)
        if add_no:
            nodes_add_no.append(node)

    # Add yes/no nodes and write file with new ids for future reference
    added_node_ids = ""
    for node in nodes_add_yes:
        new_node = create_new_node(
            "yes",
            source="yes_no_population",
            parent_id=node,
            species="yes",
            commit=False,
        )
        added_node_ids += (
            str(new_node.id) + "\t" + list(get_node_utterances(node.id))[0] + "\tyes\n"
        )
    for node in nodes_add_no:
        new_node = create_new_node(
            "no", source="yes_no_population", parent_id=node, species="no", commit=False
        )
        added_node_ids += (
            str(new_node.id) + "\t" + list(get_node_utterances(node.id))[0] + "\tno\n"
        )
    with open("added_node_ids.txt", "w") as the_file:
        the_file.write(added_node_ids)


add_yes_no_nodes()
