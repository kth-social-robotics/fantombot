import random

from fantom_util import mturk
from fantom_util.constants import TAG_ATTRIBUTES, SPECIES_TAG
from fantom_util.database import db_session
from fantom_util.database.models import (
    Worker, Job, Node, NodeUtterance,
    NodeUtteranceWorkerJob, NodeUtteranceStatus,
    IncoherentNodeUtteranceWorkerJob,
    JobNodeUtterance)
from fantom_util.graph_tools.node_tools import create_new_node, add_utterance_to_node
from fantom_util.misc import get_persona_sample, tag_matcher
from sqlalchemy.orm import joinedload
import logging

logger = logging.getLogger(__name__)

MAX_DIALOGUE_HISTORY = 6
MAX_EXTRA_QUESTIONS = 4
ALLOWED_SOURCES = [
    'typed', 'alexa', 'automatic_population', 'manual_population', 'manual',
    'space_stuff', 'manual_worldcup', 'yes_no_population', 'synonym_population'
]


def get_job(ext_job_id):
    return db_session.query(Job).filter(Job.external_id == ext_job_id).first()


def get_history(job_id):
    return db_session.query(Job).get(job_id).node_utterances


def get_worker_answer(assignment_id):
    node_utterance_worker_job = db_session.query(NodeUtteranceWorkerJob).filter(
        NodeUtteranceWorkerJob.assignment_id == assignment_id
    ).first()
    return node_utterance_worker_job.node_utterance if node_utterance_worker_job else None


def _check_node_utterance_eligibility(node_utterance, is_last_node, job_type):
    if 'incoherent' in [x.status for x in node_utterance.statuses if x.handled]:
        logger.info(f'Incoherent node_id: {node_utterance.node.id} node_utterance_id: {node_utterance.id}')
        return False
    if is_last_node and node_utterance.source not in ALLOWED_SOURCES:
        logger.info(f'last node is not allowed: {node_utterance.source}, {node_utterance.node.id} node_utterance_id: {node_utterance.id}')
        return False
    if node_utterance.source in ['automatic_population', 'alexa'] and not node_utterance.utterance.amazon_anonymous:
        logger.info(f'{node_utterance.source} anonymous: {node_utterance.utterance.amazon_anonymous} {node_utterance.node.id} node_utterance_id: {node_utterance.id}')
        return False
    if job_type != 'tag' and node_utterance.node.species == SPECIES_TAG:
        logger.info(f'skipped {node_utterance.utterance.utterance_text} as it contains tags')
        return False
    if 'yes' in [x.utterance_text for x in node_utterance.node.utterances] and node_utterance.utterance.utterance_text != 'yes':
        return False
    if 'no' in [x.utterance_text for x in node_utterance.node.utterances] and node_utterance.utterance.utterance_text != 'no':
        return False

    return True


def create_jobs(job_type, amount=1):
    if job_type not in ['user', 'system', SPECIES_TAG]:
        raise Exception('work type: "{}" does not exist. Use either system_task or user_task')

    job_filter = [Node.active_child_count == 0, Node.visited_count > 1]
    if job_type == SPECIES_TAG:
        job_filter = [Node.species == SPECIES_TAG, Node.active_child_count < 3]

    nodes = db_session.query(Node) \
        .filter(
            Node.score > 0,
            Node.is_user == (job_type != 'user'),
            Node.active.is_(True),
            *job_filter
        )\
        .order_by(Node.score.desc()) \
        .all()
    created_jobs = []
    for node in nodes:
        history_ids = node.path[-MAX_DIALOGUE_HISTORY:]
        history = db_session\
            .query(Node)\
            .filter(Node.id.in_(history_ids), Node.active.is_(True))\
            .options(joinedload(Node.utterances), joinedload(Node.node_utterances))\
            .order_by(Node.path_length.asc())\
            .all()
        history_length = len(history)
        if len(history_ids) != history_length:
            logger.warning(f'history_ids != history, {history_ids} != {history}')
            continue

        job_node_utterances = []

        for index, history_node in enumerate(history):
            pool_of_node_utterances = []
            for node_utterance in history_node.node_utterances:
                if _check_node_utterance_eligibility(node_utterance, index == history_length - 1, job_type):
                    pool_of_node_utterances.append(node_utterance)
            if pool_of_node_utterances:
                job_node_utterances.append(random.choice(pool_of_node_utterances))
        if len(history_ids) == len(job_node_utterances):
            job = Job(job_type=job_type, persona_sample=get_persona_sample())
            db_session.add(job)
            db_session.flush()
            for i, node_utterance in enumerate(job_node_utterances):
                db_session.add(JobNodeUtterance(job_id=job.id, node_utterance_id=node_utterance.id, position=i))

            created_jobs.append(job)

        if len(created_jobs) == amount:
            break
    db_session.commit()
    print(f'created {len(created_jobs)} jobs')
    return created_jobs


def check_eligibility_for_worker(job_id, external_worker_id):
    job = db_session.query(Job).get(job_id)

    if db_session.query(IncoherentNodeUtteranceWorkerJob).filter(IncoherentNodeUtteranceWorkerJob.job_id == job_id).first():
        return False

    if db_session.query(NodeUtteranceWorkerJob).filter(NodeUtteranceWorkerJob.job_id == job_id).first():
        return False

    worker = db_session.query(Worker).filter(Worker.external_worker_id == external_worker_id).first()
    if not worker:
        return True
    node_utterance_worker_job = db_session.query(NodeUtteranceWorkerJob).filter_by(worker_id=worker.id, job_id=job.id).first()
    if node_utterance_worker_job:
        return False
    workers = []
    for node_utterance in job.node_utterances:
        if node_utterance.node_utterance_worker_job:
            print(node_utterance.node_utterance_worker_job)
            workers.append(node_utterance.node_utterance_worker_job.worker)

    return worker not in workers


def _trim_sentence(text: str) -> str:
    splitted_text = text.split('.')
    return '. '.join(splitted_text[:min(2, len(splitted_text))])


def _create_or_get_worker(external_worker_id, source=None):
    worker = db_session.query(Worker) \
        .filter_by(external_worker_id=external_worker_id) \
        .first()
    if not worker:
        worker = Worker(external_worker_id=external_worker_id, source=source)
        db_session.add(worker)
        db_session.flush()
    return worker


def finish_job(ext_job_id, external_worker_id, answer, corrections, extra_questions,
               with_audio, used_text_input, assignment_id, hit_id):
    job = get_job(ext_job_id)
    nodes = [x.node for x in job.node_utterances]

    last_node = nodes[-1] if nodes else None
    worker = _create_or_get_worker(external_worker_id)

    node = create_new_node([answer], parent_id=last_node.id, source='typed')
    node_utterance = node.node_utterances[0]
    node_utterance.with_audio = with_audio
    node_utterance.used_text_input = used_text_input

    node_utterance_worker_job = NodeUtteranceWorkerJob(
        node_utterance_id=node_utterance.id,
        worker_id=worker.id,
        job_id=job.id,
        assignment_id=assignment_id,
        hit_id=hit_id
    )
    db_session.add(node_utterance_worker_job)

    for old_node_utterance_id, corrected_text in corrections.items():
        old_node_utterance = db_session.query(NodeUtterance).get(old_node_utterance_id)
        add_utterance_to_node(corrected_text, old_node_utterance.node, 'correction')
        node_utterance_status = NodeUtteranceStatus(
            node_utterance_id=old_node_utterance.id,
            status='corrected'
        )
        db_session.add(node_utterance_status)

    for extra_question in extra_questions:
        if extra_question['type'] != 'api':
            extra_node_utterance = db_session.query(NodeUtterance).get(extra_question['id'])
            for status in ['suitable', 'equivalent', 'needs_correction']:
                if extra_question[status]:
                    db_session.add(NodeUtteranceStatus(
                        node_utterance_id=extra_node_utterance.id,
                        referenced_node_utterance_id=node_utterance.id,
                        status=status
                    ))

        else:
            # extra_node_utterance = add_utterance_to_node(
            #     extra_question['text'], node, extra_question['id']
            # )
            pass


    # TODO: set positive scoring for worker and node_utterances
    db_session.commit()


def set_incoherent(ext_job_id, external_worker_id, incoherent_node_utterance_id, with_audio, assignment_id, hit_id):
    job = get_job(ext_job_id)
    worker = _create_or_get_worker(external_worker_id)

    incoherent_node_utterance = db_session.query(NodeUtterance).get(incoherent_node_utterance_id)

    incoherent_node_utterance_worker_job = IncoherentNodeUtteranceWorkerJob(
        node_utterance_id=incoherent_node_utterance.id,
        worker_id=worker.id,
        job_id=job.id,
        assignment_id=assignment_id,
        hit_id=hit_id
    )
    db_session.add(incoherent_node_utterance_worker_job)

    node_utterance_status = NodeUtteranceStatus(
        with_audio=with_audio,
        node_utterance_id=incoherent_node_utterance.id,
        status='incoherent'
    )
    db_session.add(node_utterance_status)

    # TODO: set negative scoring for worker and node_utterances

    db_session.commit()


def get_tag_attributes(history):
    tag_set = []
    item = history[-1]
    if item.node.species == SPECIES_TAG:
        for tag, index, attribute in tag_matcher(item.utterance.utterance_text):
            tag_info = TAG_ATTRIBUTES.get(tag)
            if (tag, index, None) not in tag_set:
                tag_set.append((tag, index, None))
            if tag_info:
                for attribute in tag_info['attributes'].keys():
                    if (tag, index, attribute) not in tag_set:
                        tag_set.append((tag, index, attribute))
    return tag_set


def check_for_worker_eligibilitiy_for_qualification():
    workers = db_session.query(Worker).filter(Worker.has_more_than_20_qualifaction.is_(False), Worker.source == 'mturk').all()
    for worker in workers:
        if worker.job_counts > 20:
            mturk.qualify_worker_for_has_more_than_20_qualification(worker.external_worker_id)
            worker.has_more_than_20_qualifaction = True
            db_session.commit()