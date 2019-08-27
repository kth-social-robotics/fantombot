from flask import Blueprint, render_template, redirect, url_for, request
import traceback
from fantom_util import mturk
from controllers import training_controller

training_app = Blueprint("training", __name__)
CONTACT_EMAIL = "<INSERT_EMAIL@EXAMPLE.COM>"


@training_app.route("/set_trainer")
def set_trainer() -> str:
    training_url = url_for("training.training")
    return f"""
        <form action="{training_url}" method="get">
            <input type="text" name="external_worker_id" placeholder="your worker ID">
            <input type="submit" value="submit">
        </form>
    """


@training_app.route("/done")
def done():
    return "Congratulations! You are now qualified for the HIT!"


@training_app.route("/")
def training():
    external_worker_id = request.args.get("external_worker_id")
    if not external_worker_id:
        return redirect(url_for("training.set_trainer"))

    training = training_controller.get_next_training_for_worker(external_worker_id)

    if training == "__DONE__":
        return redirect(url_for("training.done"))

    if not training or training["id"] == 0:
        return render_template(
            "video.html", task_id=0, external_worker_id=external_worker_id
        )
    else:
        return render_template(
            "training.html",
            history=training["history"],
            replies=training["replies"],
            description=training["description"],
            task_id=training["id"],
            external_worker_id=external_worker_id,
            submit_url=url_for("training.training_submit"),
            with_audio=False,
            used_text_input=True,
        )


@training_app.route("/training_submit", methods=["POST"])
def training_submit():
    external_worker_id = request.form["external_worker_id"]
    task_id = int(request.form["task_id"])
    if task_id == 0:
        the_time = float(request.form.get("task_identifier", 0.0)) - 3315.2
        if the_time < 0.9 or the_time > 1.0:
            return "Please watch the whole video and try again."

    try:
        done_training = training_controller.submit(external_worker_id, task_id)
    except KeyError:
        return redirect(
            url_for("training.training", external_worker_id=external_worker_id)
        )
    except Exception:
        print(traceback.format_exc())
        return "Sorry! Something went wrong. Please email {} and provide your worker id to fix this issue.".format(
            CONTACT_EMAIL
        )

    if done_training:
        try:
            mturk.qualify_worker(external_worker_id)
            return redirect(url_for("training.done"))
        except Exception:
            print(traceback.format_exc())
            return "You are done, but something went wrong with your qualification. Please email {} and provide your worker id to fix this issue.".format(
                CONTACT_EMAIL
            )
    else:
        return redirect(
            url_for("training.training", external_worker_id=external_worker_id)
        )
