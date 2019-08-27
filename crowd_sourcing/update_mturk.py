import sys

from controllers import job_controller
from fantom_util import mturk
import logging

from fantom_util.constants import HITS_TO_POST, SPECIES_TAG
from fantom_util.fantom_logging import create_sns_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(create_sns_logger())

hits = mturk.get_all_hits()
mturk.prune(hits)

job_controller.check_for_worker_eligibilitiy_for_qualification()

tag_job = job_controller.create_jobs(SPECIES_TAG)
if tag_job:
    mturk.make_external_hit(tag_job[0])


count_assignable = 0
for hit in hits:
    if hit['HITStatus'] == 'Assignable':
        count_assignable += 1

num_new_hits = HITS_TO_POST - count_assignable
for job in job_controller.create_jobs('system', amount=num_new_hits):
    mturk.make_external_hit(job)
