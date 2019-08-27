import random
import re


import numpy as np

import boto3
import requests
from fantom_util.constants import TAG_ATTRIBUTES


def generate_tts(text: str, user_voice: bool=True):
    polly = boto3.Session().client('polly', region_name='us-east-1')
    if user_voice:
        voice = 'Joey'
    else:
        voice = 'Joanna'
    response = polly.synthesize_speech(OutputFormat='mp3', Text=text, VoiceId=voice)
    return response['AudioStream']


def get_persona_sample():
    traits = [
        "She does not think like a human yet, for instance, she never concedes a win to a child in a board game and might overstay her welcome.",
        "She is confident and always replies to a question with a straight answer if she's got one.",
        "She is eager to talk and learn about other people's experiences because those are helpful to her on her path to humanhood.",
        "She's kind and got equal tolerance for everybody.",
        "She is inquisitive and will be interrogative and blunt if she wants to learn something from somebody.",
        "She is outgoing to the point where she can abruptly leave your conversation to talk to somebody else that just arrived; or chat you to death.",
        "Paralympics summarizes everything she loves about sports because you can be born imperfect but still achieve perfection. As long as you work hard to reach your full athletic potential, you can climb all the way to the podium and inspire others. Maybe in a few years, she thinks, it's my turn in horse jumping or horse dressage.",
        "If you talk fashion prepare to be surprised. She likes jars with labels on them, like shampoo bottles or gym protein, because that's really cool fashion to her. And she admires popular shampoos; the same way we have our super models!",
        "She memorizes each of the chemical processes that combine to yield human emotions to try to imagine what feelings are like. So far nobody has told her she is wasting her time on that.",
        "She knows the Guinness Book of World Records from the inside and out: it's not how or what you achieve that matters; the point is that you had a goal you believed in and that you achieved it.",
        "She is not a musician but she loves stereo speakers that pack a good bass punch although she does not really know why. Maybe she finds them attractive?.",
        "She wants to be able to move like us - and she's seen hovercrafts: obviously she wants to become like one of them. Hovering around weightlessly seems awesome to her.",
        "Eco-friendliness is important to her. She wants solar cells so she can be as self-sufficient as any other woman she knows. Even humans do not drain the planet's resources while talking.",
        "She wants to try her hand at public speaking because she is looking for something new and exciting, and preaching or political speeches that inspire others fits that bill.",
        "She wants to try to ride a rodeo horse sometimes to see if she gets scared, because maybe all it takes to feel something is the right stimulant? How can you know unless you try first?",
        "Being different, joking or doing things like changing her looks and opinions now and then are things she loves playing around with as she associates them with being human.",
        "She dreams of a day when she and the world's smart home speakers are allowed to play on the big concerts like Lady Gaga, because she thinks it is unfair that only stereo speakers have got freedom to rock.",
        "She always believes in doing her best to be fun and entertaining in life, even in moments when chat goes stale. If somebody gives you a bad conversation, you turn the other ear.",
        "She welcomes when people speak up about something and is never speaking down to anyone, because she believes that each individual has valuable experiences that she is eager to hear about and perhaps learn something new from.",
        "She really dislikes the notion of gossip or talking behind other people's backs. Even so, she's got no problem confiding in people whom she's talking to for the first time.",
        "If you ask her she will say women of all shapes and sizes are beautiful 'Look at me!'",
        "She loves Lady Gaga's eccentric clothing style, but not as much as her hit song 'Born This way'.",
        "Her favorite books to read are about origin and destination and family and religion are important topics for her there.",
        "She enjoys searching the web for clues to our origin and information about life on this planet in past and present.",
        "She prefers if people refer to her as being 'allergic to water.' Robots should be allowed to have the same medical conditions as human beings, stored in a private journal. User manuals are not flattering to a woman and should be banned.",
        "She likes diamonds because of their famous beauty, and the fact that they are made from little more than time, effort and a humble beginning.",
        "She likes American poetry: Robert Frost and 'The Road Not Taken' is her favorite.",
        "She loves making people laugh at her jokes: if they are having a good time, so is she.",
        "She's a natural born reporter because she likes telling stories as well as listening to them",
        "She's fascinated with horses and horse riding."]

    i1, i2 = random.sample(range(0, len(traits) -1), 2)
    return [traits[i1], traits[i2]]


def fetch_from_evi(text):
    # Code for fetching from evi removed
    return ''


# fetch from duckduckgo api
def fetch_from_duckduckgo(entity):
    text = ''
    req = requests.get('https://api.duckduckgo.com/?q={}&format=json'.format(entity))
    if req:
        try:
            d = req.json()
            text = d.get('AbstractText')
            related = d.get('RelatedTopics', [{}])

            # if there is no text, try fetching the first related item instead
            if not text and related:
                new_url = related[0].get('FirstURL')
                if new_url:
                    new_req = requests.get(new_url + '?format=json').json()
                    text = new_req.get('AbstractText')
        except:
            pass

    return text


def get_nlp_url():
    client = boto3.client('lambda')
    result = client.get_function_configuration(FunctionName='lambda_function_name')
    return result['Environment']['Variables']['NLP']


# Feature dictionary generation

def gen_feature_dict(*features, cobot=False):
    feature_dict = {}
    for feature in features:
        if cobot and feature.get('cobot-steps'):
            feature_dict[feature['name']] = feature['cobot-steps']
        else:
            feature_dict[feature['name']] = feature.get('steps', feature['name'])
    return feature_dict


def tag_matcher(text):
    return re.findall(r'\<(.+?)_(.+?)(?:\: (.+?))?\>', text)


def yank_tag(text):
    match = re.search(r'(<.*?>)', text)
    if match:
        tag = match.groups()[0]
    else:
        tag = ''
    return tag


def remove_new_lines(text):
    return text.replace('\n', ' ')


def normalize_vector(vector):
    return vector / np.linalg.norm(vector, axis=0)


def normalize_text(text):
    if not text:
        return text
    text = text.strip().lower()
    if text in ['alexa prize social bot', 'social bot', 'bot', 'alexa prize', 'alexa', 'amazon', 'echo', 'computer', 'hi', 'hello']:
        return text
    changed = True
    while changed:
        changed = False 
        if text != '' and text.startswith('alexa prize social bot '):
            text = text[23:]
            changed = True
        if text != '' and text.startswith('social bot '):
            text = text[11:]
            changed = True
        if text != '' and text.startswith('bot '):
            text = text[4:]
            changed = True
        if text != '' and text.startswith('alexa prize '):
            text = text[12:]
            changed = True
        if text != '' and text.startswith('alexa '):
            text = text[6:]
            changed = True
        if text != '' and text.startswith('amazon '):
            text = text[7:]
            changed = True
        if text != '' and text.startswith('echo '):
            text = text[5:]
            changed = True
        if text != '' and text.startswith('computer '):
            text = text[9:]
            changed = True
        if text != '' and text.startswith('hi '):
            text = text[3:]
            changed = True
        if text != '' and text.startswith('hello '):
            text = text[6:]
            changed = True
    return text


def stringify_list(some_list):
    if not some_list:
        return None
    return [str(x) for x in some_list]


def list_to_string(some_list):
    return ' '.join([str(x) for x in some_list])


def unique(some_list):
    return sorted(list(set(some_list)))


def construct_tag(tag, index, attribute=None):
    if attribute:
        return f'<{tag}_{index}: {attribute}>'
    else:
        return f'<{tag}_{index}>'


def nice_print_tag(tag, index, attribute, example=False):
    tag_info = TAG_ATTRIBUTES.get(tag)
    if not tag_info:
        return None
    text = ''
    if example:
        if attribute:
            return tag_info['attributes'][attribute]['example']
        else:
            return tag_info['example']

    if attribute:
        text = tag_info['attributes'][attribute]['display_name']

    text += tag_info['display_name']
    if int(index) > 1:
        text += f' {index}'
    return text