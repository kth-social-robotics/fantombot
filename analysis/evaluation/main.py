import os
import random
import re
import json
import shutil
import time
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


generate_td_input = """<td><input type="radio" name="{name}" class="radiobutton" oninput="answerRadio('{name}', {i})" value="{i}"></td>""".format

NAMES = [
    "Sharon",
    "Betty",
    "William",
    "Kimberly",
    "Jennifer",
    "Michael",
    "James",
    "Susan",
    "Richard",
    "Sharon",
    "Helen",
    "Margaret",
    "Nancy",
    "Michael",
    "Deborah",
    "Elizabeth",
    "John",
    "Mary",
    "Karen",
    "Ruth",
    "Jessica",
    "Robert",
    "David",
    "Laura",
    "Carlton",
    "Tanisha",
    "Jamie",
    "Andrea",
    "Sarah"
]


@app.template_filter("annotation_filter")
def annotation_filter(s):
    s = s.lower()
    s = re.sub(r"[^\x00-\x7f]", r"", s)
    s = re.sub(r"((alexa),?)", random.choice(NAMES).lower() + ',', s)
    s = re.sub(r"@\w+", random.choice(NAMES).lower(), s)
    s = re.sub(r"\s(,|\.|\?|!)", r"\1", s)
    s = re.sub(r"(,|\.)(\w)", r"\1 \2", s)
    return s


def generate_radio(name, question, red, yellow, green):
    colors = ["red", "yellow", "green"]
    abc = list(zip(colors, [red, yellow, green]))
    top = "".join(
        [
            "".join([f"<td>{rating}</td>" for rating in ratings])
            for color, ratings in abc
        ]
    )

    bottom = []
    i = 0
    for color, ratings in abc:
        for _ in ratings:
            bottom.append(generate_td_input(color=color, name=name, i=i))
            i += 1

    bottom = "".join(bottom)

    return f'<table id="{name}" cellpadding="10" cellspacing="0" width=1000 border=1><tr><td width=300 rowspan=2>{question}</td>{top}</tr><tr>{bottom}</tr></table>'


def de_dup(f, delimiter="\t"):
    for line in f:
        yield delimiter.join(field for field in line.split(delimiter) if field)


@app.route("/new", methods=["POST"])
def new():

    try:
        with open("evaluation/participants.json", "r") as f:
            participants = json.load(f)
    except FileNotFoundError:
        participants = []
    annotation_set = len(participants)

    with open("evaluation/participants.json", "w") as f:
        participants.append(
            {
                "annotation_set": str(annotation_set),
                "date": datetime.now().isoformat(),
                "name": request.form["name"],
                "department": request.form["department"],
                "email": request.form["email"],
                "age": request.form["age"],
                "gender": request.form["gender"],
                "experience": request.form["experience"],
            }
        )
        json.dump(participants, f)

    return redirect(url_for("annotate", annotation_set=annotation_set))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/annotate/<int:annotation_set>")
def annotate(annotation_set):
    found_not_done = False
    with open("evaluation/annotations_data_results.json") as f:
        dddd = json.load(f)[str(annotation_set)]
        for i, data in enumerate(dddd):
            if not data["done"]:
                found_not_done = True
                break
    if found_not_done:
        return render_template(
            "annotate.html",
            annotation_row=i,
            annotation_set=annotation_set,
            ramdom_corpus=data["dataset_name"],
            random_row=data["row_in_corpora"],
            user_utterance=data["user_utterance"],
            system_utterance=data["system_utterance"],
            debug=request.args.get("debug") == "1",
            total_length=len(dddd),
        )
    else:
        return "All done! Thanks"


@app.route("/submit", methods=["POST"])
def submit():

    while os.path.isfile("evaluation/annotations_data_results_processing.json"):
        time.sleep(0.5)

    shutil.move(
        "evaluation/annotations_data_results.json",
        "evaluation/annotations_data_results_processing.json",
    )
    try:
        with open("evaluation/annotations_data_results_processing.json") as f:
            data = json.load(f)

        data[str(request.form["annotation_set"])][
            int(request.form["annotation_row"])
        ].update(
            {
                "done": True,
                "date": datetime.now().isoformat(),
                "likely_user_utterance": int(request.form["user"]),
                "coherent_system_utterance": int(request.form.get("system", -1)),
                "interesting_system_utterance": int(request.form.get("system_2", -1)),
                "continue_system_utterance": int(request.form.get("system_3", -1)),
            }
        )

        with open("evaluation/annotations_data_results_processing.json", "w") as f:
            json.dump(data, f)
    finally:
        shutil.move(
            "evaluation/annotations_data_results_processing.json",
            "evaluation/annotations_data_results.json",
        )

    return redirect(url_for("annotate", annotation_set=request.form["annotation_set"]))


app.jinja_env.globals.update(generate_radio=generate_radio)
