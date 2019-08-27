from fantom_util.database import db_session
from fantom_util.database.models import Worker, Training, NodeUtterance, Utterance
import json


with open('training_data.json', 'r') as f:
    TRAINING_DATA = json.loads(f.read())
TASK_IDS = [x['id'] for x in TRAINING_DATA]


def get_next_training_for_worker(external_worker_id):
    worker = db_session.query(Worker) \
        .filter_by(external_worker_id=external_worker_id) \
        .first()

    training = db_session.query(Training).filter_by(worker=worker).first()

    if not training or not training.tasks:
        return None

    remaining_tasks = set(TASK_IDS) - set(training.tasks)
    if not remaining_tasks:
        return '__DONE__'

    lowest_id_for_non_perfomed_task = min(remaining_tasks)

    t = list(filter(lambda x: x['id'] == lowest_id_for_non_perfomed_task, TRAINING_DATA))[0]

    return {
        'id': t['id'],
        'history': [NodeUtterance(utterance=Utterance(utterance_text=x['text'])) for x in t['history']],
        'replies': t['replies'],
        'description': t['description']
    }


def submit(external_worker_id, task_id):
    if task_id not in TASK_IDS:
        raise KeyError('Task id not recognized')

    worker = db_session.query(Worker) \
        .filter_by(external_worker_id=external_worker_id) \
        .first()
    if not worker:
        worker = Worker(external_worker_id=external_worker_id)
        db_session.add(worker)
        db_session.commit()

    training = db_session.query(Training).filter_by(worker=worker).first()

    if not training:
        training = Training(worker=worker)
        db_session.add(training)
        db_session.commit()

    if task_id == min(set(TASK_IDS) - set(training.tasks)):
        training.tasks = training.tasks + [task_id]
        db_session.commit()

    new_set = set(TASK_IDS) - set(training.tasks)

    if not new_set:
        return True
    else:
        return False
