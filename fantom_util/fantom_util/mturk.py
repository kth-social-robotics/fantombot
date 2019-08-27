import json
import os
import re

import boto3
from fantom_util.constants import SPECIES_TAG
from fantom_util.database import db_session
from fantom_util.database.models import Job

if os.environ.get('MTURK_LIVE') == 'true':
    MTURK_URL = 'https://mturk-requester.us-east-1.amazonaws.com'
    PREVIEW_URL = "https://www.mturk.com/mturk/preview?groupId="
    MASTERS_QUALIFICATION = '2F1QJWKUDD8XADTFD2Q0G6UTO95ALH'
    INTRO_QUALIFICATION = 'SOME_MTURK_ID'
    WORKER_HITSAPPROVED = "00000000000000000040"
    WORKER_PERCENTAPPROVED = "000000000000000000L0"
    MORE_THAN_20_TASKS = 'SOME_MTURK_ID'

else:
    MTURK_URL = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
    PREVIEW_URL = "https://workersandbox.mturk.com/mturk/preview?groupId="
    MASTERS_QUALIFICATION = '2ARFPLSP75KLA8M8DH1HTEQVJT3SY6'
    INTRO_QUALIFICATION = 'SOME_MTURK_ID'
    WORKER_HITSAPPROVED = "00000000000000000040"
    WORKER_PERCENTAPPROVED = "000000000000000000L0"
    MORE_THAN_20_TASKS = "SOME_MTURK_ID"



print('using following urls:')
print(MTURK_URL)
print(PREVIEW_URL)
print('---------------------')


def connect_mturk():
    # set up mturk
    session = boto3.Session()
    return session.client('mturk', region_name='us-east-1', endpoint_url=MTURK_URL)


def create_qualification():
    mturk = connect_mturk()
    response = mturk.create_qualification_type(
        Name='Has taken introduction',
        Description='Has taken introduction',
        QualificationTypeStatus='Active'
    )
    print(response)



def make_external_hit(job):
    if job.job_type == 'system':
        create_hit_at_mturk(
            title='Continue Dialogues for Conversational AI Research (est. $8/hour)',
            description= """
                This HIT offers you the opportunity to contribute to our university research in Conversational AI.
                In the task you are asked to continue a dialogue while enacting a smart speaker device (such as Amazon Echo, or Google home, or Siri) and at the same time taking on a given personality.
                Each task is estimated to take 90 seconds to complete, but we set the maximum alloted time to 15 minutes for your convenience. We will be posting a large amount of this HIT, which has an expected hourly wage of $8 given that you complete each task in the estimated 90 seconds.
                This HIT requires that you receive a qualification. This can be done by going through our introduction task, which takes about 5 minutes to complete. Also, please make sure to 
                read and follow the persona outlined on the right side of the task for each new HIT. 
                \n\n The introduction can be found at: https://tasks.yoururl.com/training
            """,
            reward='0.20',
            job=job,
            local_requirements=[
                {'QualificationTypeId': '00000000000000000071', 'Comparator': 'EqualTo', 'LocaleValues': [{'Country': 'US'}], 'RequiredToPreview': False},
                {'QualificationTypeId': WORKER_HITSAPPROVED, 'Comparator': 'GreaterThan', 'IntegerValues': [5000], 'RequiredToPreview': False},
                {'QualificationTypeId': WORKER_PERCENTAPPROVED, 'Comparator': 'GreaterThan', 'IntegerValues': [97], 'RequiredToPreview': False},
                {'QualificationTypeId': INTRO_QUALIFICATION, 'Comparator': 'Exists', 'RequiredToPreview': False}
            ]
        )
    elif job.job_type == SPECIES_TAG:
        create_hit_at_mturk(
            title='Continue Dialogues for Conversational AI Research [special task] (est. $12/hour)',
            description="""
                        ONLY WORKS ON MODERN BROWSERS! Supported browsers are: Firefox 50+, Opera 39+, Google Chrome 51+ and Microsoft Edge 16+ or Safari 11+
                        This HIT offers you the opportunity to contribute to our university research in Conversational AI.
                        In the task you are asked to continue a dialogue while enacting a smart speaker device (such as Amazon Echo, or Google home, or Siri) and at the same time taking on a given personality.
                        For the purpose of handling named entities in conversations, such as names of movies, musicians, etc., we added a new mechanism to our system - tags. 
                        A tag represents a named entity of a certain category, e.g. a sentence 'I love [Movie Title]' would in conversation be transformed to 'I love Blade Runner'. 
                        Furthermore, we have provided you with additional information about the named entity, that we encourage you to utilise when creating responses. 
                        For movies, you can talk about the director, main actor or genre. 
                        You will see the list of the available tags you can use for a given utterance as boxes that you can drag and drop into the sentence, or just click on them and they will be inserted at where your cursor is at.
                        Each task is estimated to take 90 seconds to complete, but we set the maximum alloted time to 15 minutes for your convenience. We will be posting a large amount of this HIT, which has an expected hourly wage of $12 given that you complete each task in the estimated 90 seconds.
                        This HIT requires that you receive a qualification. This can be done by completening 20 tasks that have been accepted for our other task. Also, please make sure to 
                        read and follow the persona outlined on the right side of the task for each new HIT.
                    """,
            reward='0.30',
            job=job,
            local_requirements=[{'QualificationTypeId': MORE_THAN_20_TASKS, 'Comparator': 'Exists', 'RequiredToPreview': False}]
        )


def create_hit_at_mturk(title=None, description=None, reward=None, job=None, local_requirements=None):
    keywords = 'text, quick, chat, conversational ai'
    question = """
        <ExternalQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2006-07-14/ExternalQuestion.xsd">
            <ExternalURL>https://tasks.yoururl.com/create_content/mturk/{}</ExternalURL>
            <FrameHeight>1000</FrameHeight>
        </ExternalQuestion>
    """.format(str(job.external_id))

    mturk = connect_mturk()
    mturk.create_hit(
        Title=title,
        Description=description,
        Keywords=keywords,
        Reward=reward,
        MaxAssignments=1,
        LifetimeInSeconds=3300,
        AssignmentDurationInSeconds=900,
        Question=question,
        RequesterAnnotation=json.dumps({'ext_job_id': str(job.external_id)}),
        QualificationRequirements=local_requirements
    )


def get_hit_info(hit_id):
    mturk = connect_mturk()
    hit_info = mturk.get_hit(HITId=hit_id)
    assignments = mturk.list_assignments_for_hit(HITId=hit_id)
    if assignments['Assignments']:
         assignment = assignments['Assignments'][0]
    else:
        return None
    annotation = hit_info.get('HIT', {}).get('RequesterAnnotation')
    if annotation:
        ext_job_id = json.loads(annotation).get('ext_job_id')
        if not ext_job_id:
            ext_job_id = db_session.query(Job).get(int(json.loads(annotation).get('job_id'))).external_id
    else:
        result = re.search(r'<Answer><QuestionIdentifier>ext_job_id<\/QuestionIdentifier><FreeText>(\d*)<\/FreeText><\/Answer>', assignment['Answer'])
        if result:
            ext_job_id = result.group(1)
        else:
            result = re.search(r'<Answer><QuestionIdentifier>job_id<\/QuestionIdentifier><FreeText>(\d*)<\/FreeText><\/Answer>', assignment['Answer'])
            job_id = result.group(1)
            ext_job_id = db_session.query(Job).get(int(job_id)).external_id

    incoherent_result = re.search(r'<Answer><QuestionIdentifier>incoherent-dialog-box</QuestionIdentifier><FreeText>(\d*)</FreeText></Answer>', assignment['Answer'])
    answer = {}
    if incoherent_result:
        answer['incoherent'] = int(incoherent_result.group(1))

    answer_result = re.search(r'<Answer><QuestionIdentifier>answer</QuestionIdentifier><FreeText>(.*)</FreeText></Answer>', assignment['Answer'])

    if answer_result:
        answer['answer'] = answer_result.group(1)
    return {
        'description': hit_info['HIT']['Description'],
        'reward': hit_info['HIT']['Reward'],
        'title': hit_info['HIT']['Title'],
        'ext_job_id': ext_job_id,
        'assignment_id': assignment['AssignmentId'],
        'answer': answer
    }


def get_qualification_requests():
    client = connect_mturk()
    return client.list_qualification_requests()


def delete_hit(hit_id: str):
    client = connect_mturk()
    client.delete_hit(HITId=hit_id)


def approve_assignment(assignment_id: str, comment: str=None):
    client = connect_mturk()
    arguments = {
        'AssignmentId': assignment_id
    }
    if comment:
        arguments['RequesterFeedback'] = comment

    client.approve_assignment(**arguments)


def reject_assignment(assignment_id: str, comment: str):
    client = connect_mturk()
    client.reject_assignment(AssignmentId=assignment_id, RequesterFeedback=comment)


def qualify_worker(external_worker_id):
    client = connect_mturk()
    client.associate_qualification_with_worker(
        QualificationTypeId=INTRO_QUALIFICATION,
        WorkerId=external_worker_id,
        IntegerValue=1,
        SendNotification=True
    )


def qualify_worker_for_has_more_than_20_qualification(external_worker_id):
    client = connect_mturk()
    client.associate_qualification_with_worker(
        QualificationTypeId=MORE_THAN_20_TASKS,
        WorkerId=external_worker_id,
        IntegerValue=1,
        SendNotification=False
    )


def get_all_hits():
    client = connect_mturk()

    def get_stuff(token):
        the_args = {'MaxResults': 100}
        if token:
            the_args['NextToken'] = token
        return client.list_hits(**the_args)

    stuff_len = 100
    token = None
    list_of_hits = []
    while stuff_len == 100:
        new_stuff = get_stuff(token)
        list_of_hits += new_stuff['HITs']
        stuff_len = len(new_stuff['HITs'])
        token = new_stuff.get('NextToken')
    return list_of_hits


def get_balance():
    client = connect_mturk()
    return client.get_account_balance()['AvailableBalance']


def prune(hits):
    client = connect_mturk()
    for hit in hits:
        if hit['HITStatus'] == 'Reviewable' and (hit['MaxAssignments'] == hit['NumberOfAssignmentsAvailable'] or hit['MaxAssignments'] == hit['NumberOfAssignmentsCompleted']):
            client.delete_hit(HITId=hit['HITId'])
