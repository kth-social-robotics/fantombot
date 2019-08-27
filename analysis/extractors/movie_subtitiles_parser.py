import json
import random
from os import path, walk, remove, listdir, sep
import argparse, logging
import re

from xml.sax.handler import ContentHandler
from xml.sax import SAXException, make_parser

from collections import defaultdict
from operator import itemgetter

UNK = '__UNK__'


class OpenSubtitlesHandler(ContentHandler):

    def initialize(self):
        self.sentences = []
        self.in_subtitle = False
        self._charBuffer = []
        self.subtitle = {}

    def _getCharacterData(self):
        data = ''.join(self._charBuffer).strip()
        self._charBuffer = []
        return data.strip() #remove strip() if whitespace is important

    def startDocument(self):
        self.initialize()

    def startElement(self, tag, attrs):
        if tag == 's':
            #self.sentences.append([])
            self.in_subtitle = True
        if tag == 'time':
            if attrs._attrs['id'].find('S') > -1:
                self.start_time = attrs._attrs['value']
            else:
                self.end_time = attrs._attrs['value']

    def endElement(self, tag):
        if tag == 's' and self.in_subtitle:
            sentence = {'content': self._getCharacterData()}
            if hasattr(self,'end_time'):
                sentence['end_time'] = self.end_time
            if hasattr(self, 'start_time'):
                sentence['start_time'] = self.start_time
            self.sentences.append(sentence)
            self.in_subtitle = False

    def characters(self, content):
        if self.in_subtitle:
            self._charBuffer.append(content)

VOCABULARY_SIZE = 40000

def make_vocabulary(in_parsed_docs, limit=VOCABULARY_SIZE):
    wordcount = defaultdict(lambda: 0)
    for doc in in_parsed_docs:
        for sentence in doc:
            for word in sentence['content'].split():
                wordcount[word.lower() if word != 'I' else word] += 1
    wordcount_sorted = sorted(wordcount.items(), key=itemgetter(1), reverse=True)
    result = set(map(itemgetter(0), wordcount_sorted[:limit]))
    return result


def parse_corpus(text_root):
    handler = OpenSubtitlesHandler()
    xml_parser = make_parser()
    xml_parser.setContentHandler(handler)

    toplevel = [folder for folder in listdir(text_root) if path.isdir(path.join(text_root, folder)) and int(folder) > 2000]

    parsed_corpus = {}
    for root, dirs, files in walk(path.abspath(text_root)):
        for filename in files:
            logging.warning('{} directories parsed out of {}'.format(toplevel.index(root.split(sep)[-2]),
                                                                     len(toplevel)))
            if not filename.endswith('xml'):
                continue
            if filename.startswith('._'):
                logging.info('Removing osx created file {}'.format(path.join(root,filename)))
                remove(path.join(root,filename))
                continue
            full_filename = path.join(root, filename)
            try:
                xml_parser.parse(full_filename)
            except SAXException:
                logging.warning('Error parsing {}'.format(full_filename))
                continue
            parsed_corpus[full_filename] = handler.sentences
    return parsed_corpus

def remove_non_speech_events(sentence):


    clean_sentence = []
    multiple_word_event = False
    for word in sentence:
        if multiple_word_event:
            continue
        for e in re.findall(r'\{([^}]+)\}',word):
            if re.findall(r'^[a-zA-Z]+$', word.split('}')[1]):
                clean_sentence.append(word.split('}')[1])
            continue
        if re.findall(r'\((.*?)\)',word):
            continue
        if re.match('\((.*?)',word):
            multiple_word_event = True
            continue
        if re.match('(.*?)\)',word):
            multiple_word_event = False
            continue
        if re.findall(r'\[(.+?)\]',word):
            continue
        clean_sentence.append(word)

    return clean_sentence

def preprocess_os(in_parsed_docs):
    docs = in_parsed_docs.values()
    vocabulary = make_vocabulary(docs)
    filtered_get = lambda word: word if word in vocabulary else UNK
    result = []
    for content in docs:
        for sentence in content:
            processed_content = sentence
            processed_sentence = [word.lower() if word != 'I' else word for word in sentence['content'].split()]
            filtered_sentence = [filtered_get(word) for word in processed_sentence]
            filtered_sentence = remove_non_speech_events(filtered_sentence)
            processed_content['content'] = filtered_sentence
            result.append(processed_content)
    return result

def get_float_time(time_string):

    time_pattern = re.compile(r'(\d+):(\d+):(\d+),(\d+)')

    time_string = re.sub('-','',time_string)

    try:
        hour,minute,second,frac_sec = re.match(time_pattern, time_string).groups()
    except:
        hour,minute,second,frac_sec = time_string.split(':')

    return 3600*float(hour) + 60*float(minute) + float(second) + float('0.{}'.format(frac_sec))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='OpenSubs conversation loader (Based on Igor\'s one)')
    parser.add_argument('--opensubs_dir','-od',help='Path to the open subs logdir',required=True)
    parser.add_argument('--output_file','-o',help='path to the output file')

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    args = parser.parse_args()

    corpus = parse_corpus(args.opensubs_dir)

    sentence_tuples = []

    processed_text = preprocess_os(corpus)

    for s,sub in enumerate(processed_text):

        if s < len(processed_text) - 1:
            next_sub = processed_text[s+1]
        else:
            continue

        # big gap between subtitles (maybe not part of the same conversation)
        if get_float_time(next_sub['start_time'])-get_float_time(sub['end_time']) > 1 or \
                get_float_time(next_sub['start_time']) - get_float_time(sub['end_time']) < 0:
            continue

        if '-' in sub['content'] and '-' in next_sub['content'] and \
            len(sub['content']) > 6 and len(next_sub['content']) > 6 and \
            len(sub['content']) < 11 and len(next_sub['content']) < 11 and \
            '__UNK__' not in sub['content'] and '__UNK__' not in next_sub['content'] and \
            sub['content'] != next_sub['content']:

            entry = '{}\t{}'.format(' '.join(sub['content'][1:]),
                                                   ' '.join(next_sub['content'][1:]))
            if entry not in sentence_tuples:
                sentence_tuples.append(entry)

    with open('os_all.txt','w') as f:
        f.write('\n'.join(sentence_tuples))



