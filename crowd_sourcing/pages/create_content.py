import datetime
import traceback

from PIL import Image, ImageDraw, ImageOps, ImageFont
from io import BytesIO
from collections import defaultdict

from controllers import job_controller
from fantom_util import constants
from fantom_util.constants import SPECIES_TAG
from fantom_util.database import db_session
from fantom_util.misc import nice_print_tag
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    abort,
    send_file,
)
from common import requires_auth

create_content_app = Blueprint("create_content", __name__)
CONTACT_EMAIL = "<INSERT_EMAIL@EXAMPLE.COM>"


@create_content_app.route("/")
@requires_auth
def home():
    worker_id = request.args.get("workerId")
    job_type = request.args.get("job_type", "system")
    if not worker_id:
        return redirect(url_for("create_content.set_worker"))
    job = job_controller.create_jobs(job_type)
    if not job:
        return "No job could be created"
    return redirect(
        url_for("create_content.job", ext_job_id=job[0].external_id, workerId=worker_id)
    )


@create_content_app.route("/set_worker")
@requires_auth
def set_worker() -> str:
    return render_template(
        "set_worker.html",
        submit_url=request.args.get("url", url_for("create_content.home")),
        constants=constants,
    )


@create_content_app.route(
    "/image/<string:tag>/<int:index>", defaults={"attribute": None}
)
@create_content_app.route("/image/<string:tag>/<int:index>/<string:attribute>")
def generate_image(tag, index, attribute) -> str:

    example = request.args.get("example") == "true"

    text = nice_print_tag(tag, index, attribute, example)
    if not text:
        abort(404)

    byte_io = BytesIO()
    font = ImageFont.truetype("fonts/Roboto-Light.ttf", 14, encoding="unic")
    text_width, text_height = font.getsize(text)
    img = Image.new("RGB", (text_width + 10, text_height + 5), color="#ededed")
    d = ImageDraw.Draw(img)
    d.text((5, 1), text, font=font, fill="#333333")
    g = ImageOps.expand(img, border=1, fill="#d9d9d9")
    g.save(byte_io, "JPEG", quality=100)
    byte_io.seek(0)
    return send_file(byte_io, mimetype="image/jpeg")


def show_task(submit_url, ext_job_id, external_worker_id, mturk=False):
    assignment_id = request.args.get("assignmentId")
    hit_id = request.args.get("hitId")
    job = job_controller.get_job(ext_job_id)

    if job.job_type not in ["system", SPECIES_TAG] or (mturk and job.is_expired):
        abort(404)

    if job.job_type == SPECIES_TAG:
        supported_versions = (
            ("firefox", 50),
            ("opera", 39),
            ("chrome", 51),
            ("edge", 16),
            ("safari", 11),
        )
        browser = request.user_agent.browser
        browser_version = int(request.user_agent.version.split(".", 1)[0])
        if not any(
            [
                browser == supported_browser
                and browser_version >= supported_browser_version
                for supported_browser, supported_browser_version in supported_versions
            ]
        ):
            return "Sorry. You need a modern browser in order to do this task. Supported browsers are: Firefox 50+, Opera 39+, Google Chrome 51+ and Microsoft Edge 16+ or Safari 11+"

    if mturk and not job_controller.check_eligibility_for_worker(
        job.id, external_worker_id
    ):
        return """
            Sorry, you cannot do this assignment, please skip this one and
            do another one instead!
        """

    history = job_controller.get_history(job.id)
    tag_attributes = job_controller.get_tag_attributes(history)

    return render_template(
        f"questions_system.html",
        history=history,
        api_results=[],
        ext_job_id=job.external_id,
        external_worker_id=external_worker_id,
        with_audio=False,
        used_text_input=True,
        submit_url=submit_url,
        assignment_id=assignment_id,
        hit_id=hit_id,
        is_user=job.job_type == "user",
        persona_sample=job.persona_sample,
        tag_attributes=tag_attributes,
    )


@create_content_app.route("/job/<string:ext_job_id>")
@requires_auth
def job(ext_job_id):
    external_worker_id = request.args.get("workerId")
    if not external_worker_id:
        return redirect(url_for("create_content.set_worker", url=request.path))
    return show_task(
        url_for("create_content.next_task"), ext_job_id, external_worker_id
    )


@create_content_app.route("/mturk/<string:ext_job_id>")
def mturk_job(ext_job_id):
    external_worker_id = request.args.get("workerId")
    if external_worker_id != "NO_WORKER_ID":
        job_controller._create_or_get_worker(external_worker_id, source="mturk")
        db_session.commit()
    submit_url = "{}/mturk/externalSubmit".format(request.args.get("turkSubmitTo", ""))
    return show_task(submit_url, ext_job_id, external_worker_id, mturk=True)


@create_content_app.route("/next_task", methods=["POST"])
def next_task():
    external_worker_id = request.form["external_worker_id"]
    return redirect(url_for("create_content.home", workerId=external_worker_id))


@create_content_app.route("/submit", methods=["POST"])
def submit():
    ext_job_id = request.form["ext_job_id"]
    external_worker_id = request.form["external_worker_id"]
    assignment_id = request.form["assignmentId"]
    hit_id = request.form["hitId"]
    answer = request.form["answer"].strip().replace("[", "<").replace("]", ">")

    corrections = {}
    for name, value in request.form.items():
        if name.startswith("edit-previous-msg-"):
            old_node_user_id = int(name.rsplit("-", 1)[1])
            corrections[old_node_user_id] = value

    action_dict = defaultdict(list)
    extra_questions = []

    for t in ["api_call_equiv", "api_call_suitable", "api_call_needs_corrections"]:
        for service_text in request.form.getlist(t):
            action_dict[service_text].append(t)

    for service_text, checkboxes in action_dict.items():
        service, text = service_text.split("___")
        extra_question = {
            "text": text,
            "suitable": "api_call_suitable" in checkboxes,
            "equivalent": "api_call_equiv" in checkboxes,
            "needs_correction": "api_call_needs_corrections" in checkboxes
            and service_text.startswith("similar-utt-"),
        }
        if service_text.startswith("similar-utt-"):
            extra_question["id"] = int(service.rsplit("-", 1)[1])
            extra_question["type"] = "typed"
        else:
            extra_question["id"] = service
            extra_question["type"] = "api"

        extra_questions.append(extra_question)

    try:
        job_controller.finish_job(
            ext_job_id,
            external_worker_id,
            answer,
            corrections,
            extra_questions,
            False,
            True,
            assignment_id,
            hit_id,
        )
    except Exception as e:
        print(traceback.format_exc())
        return "something went wrong"
    return "ok"


@create_content_app.route("/reject_submit", methods=["POST"])
def reject_submit():
    try:
        ext_job_id = request.form["ext_job_id"]
        external_worker_id = request.form["external_worker_id"]
        incoherent_node_utterance_id = int(request.form.get("incoherent-dialog-box"))
        assignment_id = request.form["assignmentId"]
        hit_id = request.form["hitId"]

    except TypeError:
        return """
            Something went wrong. <br />
            Please try to resubmit the form,
            or contact {} if the issues persist.
        """.format(
            CONTACT_EMAIL
        )
    job_controller.set_incoherent(
        ext_job_id,
        external_worker_id,
        incoherent_node_utterance_id,
        False,
        assignment_id,
        hit_id,
    )

    return "ok"

