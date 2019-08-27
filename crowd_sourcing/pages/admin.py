import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from typing import Callable

from controllers import (
    job_controller,
    graph_controller,
    merging_controller,
    show_tree,
    conversation_controller,
)
from fantom_util import mturk
from fantom_util.database import db_session
from fantom_util.database.models import Job, Utterance
from fantom_util.graph_tools.node_tools import inactivate_node
from flask import Blueprint, render_template, request, redirect, url_for
from common import requires_auth


admin_app = Blueprint("admin", __name__)


def build_shortener(all_strings: list) -> Callable:
    shortenings = {}
    set_of_strings = set(all_strings)
    for s in sorted(set_of_strings, key=len, reverse=True):
        i = 1
        is_unique = False
        new_shortening = s
        while not is_unique and i <= len(s):
            the_slice = s[slice(0, i)]
            string_with_same_start = [
                x for x in set_of_strings if x.startswith(the_slice)
            ]
            if len(string_with_same_start) == 1:
                is_unique = True
                new_shortening = the_slice
            i += 1
        shortenings[s] = new_shortening
    return lambda x: shortenings.get(x, x)


@admin_app.route("/get_tree")
@requires_auth
def get_tree() -> str:
    return render_template("graph.html", data=graph_controller.get_graph())


@admin_app.route("/get_tree_v2")
@requires_auth
def get_tree_v2() -> str:
    return render_template("graph_v2.html")


@admin_app.route("/get_tree_v3", defaults={"node_id": None})
@admin_app.route("/get_tree_v3/<int:node_id>")
@requires_auth
def get_tree_v3(node_id) -> str:
    parents = graph_controller.get_parents(node_id)
    nodes = graph_controller.get_nodes(node_id)
    node = graph_controller.get_current_node(node_id)
    return render_template(
        "graph_v3.html", nodes=nodes, parents=parents, current_node=node
    )


@admin_app.route("/hit/<string:hit_id>")
@requires_auth
def get_tree_for_job_id(hit_id) -> str:
    hit_info = mturk.get_hit_info(hit_id)
    if not hit_info:
        return "There are no assignments for this HIT"
    job = job_controller.get_job(hit_info["ext_job_id"])
    history = job_controller.get_history(job.id)
    worker_answer = job_controller.get_worker_answer(hit_info["assignment_id"])
    return render_template(
        "hit_info.html",
        job=job,
        description=hit_info["description"],
        reward=hit_info["reward"],
        title=hit_info["title"],
        history=history,
        assignment_id=hit_info["assignment_id"],
        answer=hit_info["answer"],
        hit_id=hit_id,
        worker_answer=worker_answer,
    )


@admin_app.route("/get_qualification")
@requires_auth
def get_qualification() -> str:
    return str(mturk.get_qualification_requests())


@admin_app.route("/correct_spelling_submit", methods=["post"])
@requires_auth
def correct_spelling_submit() -> str:
    utterance_id = int(request.form["utterance_id"])
    new_spelling = request.form["new_spelling"]
    corections = request.form.get("corections")
    utterance = db_session.query(Utterance).get(utterance_id)
    utterance.utterance_text = new_spelling
    utterance.is_spellchecked = True
    db_session.commit()
    with open("new_corrections_v2.json", "r") as f:
        new_corrections = json.dumps(
            [x for x in json.loads(f.read()) if x[0] != utterance_id]
        )

    with open("new_corrections_v2.json", "w") as f:
        f.write(new_corrections)

    if corections:
        return redirect(url_for("admin.fix_spelling_issues"))
    return "ok, done! Please reload the page to see your spelling fix"


@admin_app.route("/correct_spelling/<int:utterance_id>")
@requires_auth
def correct_spelling(utterance_id) -> str:
    utterance = db_session.query(Utterance).get(utterance_id)
    url = url_for("admin.correct_spelling_submit")
    return f'<!DOCTYPE html><html><body><form method="post" action="{url}"><span style="background-color: yellow">Do not change the semantic meaning of the sentence (such as adding a question or modifying the meaning of the sentence). If you want to do that, add a new utterance instead.</span><br><input type="hidden" name="utterance_id" value="{utterance.id}"><textarea style="width: 100%; height: 50px;" name="new_spelling">{utterance.utterance_text}</textarea></form></body></html>'


@admin_app.route("/")
@requires_auth
def hidden_stuff() -> str:
    all_hits = mturk.get_all_hits()
    balance = mturk.get_balance()
    hits = []
    comleted_list = []
    count_dead_hits = 0
    priority_list = []
    shortener = build_shortener([x["HITGroupId"] for x in all_hits])
    for hit in all_hits:
        ext_job_id = json.loads(hit["RequesterAnnotation"]).get("ext_job_id")
        if not ext_job_id:
            ext_job_id = (
                db_session.query(Job)
                .get(int(json.loads(hit["RequesterAnnotation"]).get("job_id")))
                .external_id
            )
        hit["ExtJobId"] = ext_job_id
        hit["ShortHITGroupId"] = shortener(hit["HITGroupId"])
        # if hit['HITStatus'] == 'Reviewable' and hit['MaxAssignments'] == hit['NumberOfAssignmentsAvailable']:
        # count_dead_hits += 1
        if (
            hit["HITStatus"] == "Reviewable"
            and hit["MaxAssignments"] == hit["NumberOfAssignmentsCompleted"]
        ):
            comleted_list.append(hit)
        elif (
            hit["HITStatus"] == "Reviewable"
            and hit["MaxAssignments"] != hit["NumberOfAssignmentsAvailable"]
        ):
            priority_list.append(hit)
        elif hit["HITStatus"] != "Reviewable" and hit["HITStatus"] != "Assignable":
            priority_list.append(hit)
        else:
            hits.append(hit)

    return render_template(
        "hidden_stuff.html",
        hits=priority_list + comleted_list + hits,
        count_dead_hits=count_dead_hits,
        balance=balance,
    )


@admin_app.route("/delete_hit/<string:hit_id>")
@requires_auth
def delete_hit(hit_id: str) -> str:
    mturk.delete_hit(hit_id)
    return redirect(url_for("admin.hidden_stuff"))


@admin_app.route("/assess_assignment", methods=["POST"])
@requires_auth
def assess_assignment() -> str:
    assignment_id = request.form.get("assignment_id")
    if request.form.get("reject_button") and request.form.get("comment") != "":
        mturk.reject_assignment(assignment_id, request.form.get("comment"))
    elif request.form.get("approve_button"):
        mturk.approve_assignment(assignment_id, request.form.get("comment"))
    else:
        return "Something went wrong."
    return redirect(url_for("admin.hidden_stuff"))


@admin_app.route("/create_new_hits/<string:job_type>/<int:amount>")
@requires_auth
def create_new_hits(job_type: str, amount: int):
    for job in job_controller.create_jobs(job_type, amount=amount):
        mturk.make_external_hit(job)
    return redirect(url_for("admin.hidden_stuff"))


@admin_app.route("/score")
@requires_auth
def score():
    return render_template("utt.html", trees=show_tree.nodes())


@admin_app.route("/merge")
@requires_auth
def merge():
    return render_template(
        "merge.html", similar_node_pairs=merging_controller.get_merge_nodes()
    )


@admin_app.route("/merge_nodes", methods=["POST"])
@requires_auth
def merge_nodes():
    json_data = request.get_json()
    left_node_id = json_data.get("left_node_id")
    right_node_id = json_data.get("right_node_id")
    do_merge = json_data.get("merge")
    print(left_node_id, right_node_id, do_merge)
    merging_controller.merge_nodes(left_node_id, right_node_id, do_merge)
    return json.dumps({"success": True})


def merge_submit():
    merge_nodes = request.form.getlist("nodes_merge")
    all_nodes = request.form.getlist("nodes_all")
    for node in all_nodes:
        left_node_id, right_node_id = node.split("--")
        merging_controller.merge_nodes(left_node_id, right_node_id, node in merge_nodes)
        # print(left_node_id, right_node_id, node in merge_nodes)

    return redirect(url_for("admin.merge"))


@admin_app.route("/conversation_table")
@requires_auth
def conversation() -> str:
    start_time = request.args.get("start_time")
    end_time = request.args.get("end_time")
    if start_time:
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    if end_time:
        end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    ratings = conversation_controller.get_ratings(start_time, end_time)

    avg_conversation_turns = (
        sum([x.turns for x in ratings]) / len(ratings) if ratings else 0
    )

    if not start_time:
        start_time = min([x.start_time for x in ratings]).replace(hour=0, minute=0)
    if not end_time:
        end_time = max([x.start_time for x in ratings])

    all_ratings = [x.rating for x in ratings if x.rating]

    if all_ratings:
        binned_ratings_labels, binned_ratings_values = zip(
            *sorted(Counter(map(round, all_ratings)).items(), key=lambda x: x[0])
        )
        avg_rating = sum(all_ratings) / len(all_ratings)
    else:
        avg_rating = 0
        binned_ratings_labels, binned_ratings_values = [], []

    return render_template(
        "conversation_table.html",
        ratings=ratings,
        start_time=start_time,
        end_time=end_time,
        avg_conversation_turns=avg_conversation_turns,
        binned_ratings_labels=binned_ratings_labels,
        binned_ratings_values=binned_ratings_values,
        avg_rating=avg_rating,
    )


@admin_app.route("/conversation_table/<int:rating_id>")
@requires_auth
def show_conversation(rating_id) -> str:
    rating = conversation_controller.get_rating(rating_id)
    return render_template("show_conversation.html", rating=rating)


def colors(n):
    ret = []
    r = int(random.random() * 256)
    g = int(random.random() * 256)
    b = int(random.random() * 256)
    step = 256 / n
    for i in range(n):
        r += step
        g += step
        b += step
        r = int(r) % 256
        g = int(g) % 256
        b = int(b) % 256
        ret.append((r, g, b))
    return ret


@admin_app.route("/fix_spelling_issues")
@requires_auth
def fix_spelling_issues() -> str:
    with open("new_corrections_v2.json", "r") as f:
        spelling_corrections = json.loads(f.read())
        utterance_id, utterance_text, results = spelling_corrections[0]
    utterance = db_session.query(Utterance).get(utterance_id)
    if (
        utterance_text != utterance.utterance_text
        or utterance.is_spellchecked
        or not any([x.active for x in utterance.nodes])
    ):
        with open("new_corrections_v2.json", "w") as f:
            f.write(json.dumps(spelling_corrections[1:]))
        redirect(url_for("admin.fix_spelling_issues"))

    newest_text = ""
    has_started = defaultdict(bool)
    set_of_levels = set()
    matches = sorted(results["matches"], key=lambda x: x["offset"])

    for i, letter in enumerate(utterance_text):
        levels = []
        max_for_letter = 0
        lowest_reset = None

        for n, match in enumerate(matches):
            start, stop = match["offset"], match["offset"] + match["length"]
            if start <= i < stop:
                levels.append(n)
                set_of_levels.add(n)
                max_for_letter = max(max_for_letter, n)
        level_list = (
            levels
            if not levels or max_for_letter in levels
            else levels + [max_for_letter]
        )

        for val in sorted(list(set_of_levels)):
            if val not in level_list and has_started[val] and lowest_reset is None:
                lowest_reset = val

            if lowest_reset is not None and val >= lowest_reset and has_started[val]:
                newest_text += f"</span>"
                has_started[val] = False

        for val in sorted(list(set_of_levels)):
            if val in level_list and not has_started[val]:
                newest_text += f'<span class="level-{val}">'
                has_started[val] = True

        newest_text += letter

    css = {}
    for color, level in zip(colors(len(set_of_levels)), set_of_levels):
        css[level] = color

    nodes = [x.id for x in utterance.nodes]
    visit_count = sum([x.visited_count for x in utterance.nodes])

    return render_template(
        "fix_spelling_issues.html",
        utterance=utterance,
        results=enumerate(matches),
        text=newest_text,
        css=css,
        visit_count=visit_count,
        nodes=nodes,
    )


@admin_app.route("/inactivate_node/<int:node_id>", methods=["DELETE"])
@requires_auth
def inactivate_a_node(node_id):
    inactivate_node(node_id)
    return "ok"

