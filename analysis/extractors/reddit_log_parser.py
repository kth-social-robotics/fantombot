import argparse
import bz2
import json,re
from codecs import getwriter

import os,sys

import logging

import random
from tqdm import *
import mmap

l = 0
parent_ids = []

MAXIMUM_CHAIN_DEPTH = 100
DIALOGUE_SEPARATOR = '#' * 60
MAXIMUM_NUM_DIALOGUES = 200

class CommentTreeNode(object):
    def __init__(self, in_id, in_body):
        self.body = in_body
        if self.body:
            self.body = re.sub('\s', ' ', self.body.strip().lower())
        self.children = []
        self.node_id = in_id

    def adopt_child(self, in_node):
        self.children.append(in_node)

def get_num_lines(file_path):

    fp = open(file_path,'rb')
    buf = mmap.mmap(fp.fileno(), 0,access=mmap.ACCESS_READ)
    lines = 0
    while buf.readline():
        lines += 1
    return lines

def check_url(comment_content):

    urls = re.findall('/(?:[-\w.]|(?:%[\da-fA-F]{2}))+',comment_content)

    if len(urls):
        return True

    return False

def clean_comment(comment_content):

    clean_comment = re.sub('\*', '', comment_content)
    clean_comment = re.sub('"', '', clean_comment)
    clean_comment = re.sub('&gt;','', clean_comment)
    clean_comment = re.sub('\[','',clean_comment)
    clean_comment = re.sub('\]','',clean_comment)
    clean_comment = re.sub('^^^','',clean_comment)

    return re.sub('\s+',' ',clean_comment)

def write_comment_chains(in_root_node, text_output_stream, num_pairs_created, in_previous_context=[]):
    try:
        if num_pairs_created > MAXIMUM_NUM_DIALOGUES:
            return
        own_content = [] \
            if in_root_node.node_id == 0 \
            else [(in_root_node.node_id, in_root_node.body)]
        comment_chain = in_previous_context + own_content
        if (
            MAXIMUM_CHAIN_DEPTH == len(comment_chain) or
            not len(in_root_node.children)
        ):

            all_string_comments = []
            if len(comment_chain) > 2:
                for node_content in comment_chain:
                    if node_content[1] not in ['__content_missing__','[deleted]'] and \
                            not check_url(node_content[1]):
                        all_string_comments.append(node_content)

            if len(all_string_comments) > 2:
                starting_nodes = []
                # get ids
                all_ids = [node_content[0] for node_content in all_string_comments]
                all_ids = all_ids[:-2] #only uses dialogues that have a potential 3rd sentences
                while 1:
                    # randomly picking a point in the conversation
                    comment_selected = random.randint(0,len(all_string_comments)-3)
                    starting_nodes.append(all_string_comments[comment_selected][0])
                    parent_comment = clean_comment(all_string_comments[comment_selected][1])
                    seq_1_comment = clean_comment(all_string_comments[comment_selected+1][1])
                    seq_2_comment = clean_comment(all_string_comments[comment_selected+2][1])
                    # checking if all 3 utterances are long enough
                    if len(parent_comment.split()) > 5 and len(parent_comment.split()) < 11 and\
                           len(seq_1_comment.split()) > 5 and len(seq_1_comment.split()) < 11 and\
                            len(seq_2_comment.split()) > 5 and len(seq_2_comment.split()) < 11:
                        text_output_stream.write('{}\t\t{}\t\t{}\t\t{}\n'.format(all_string_comments[comment_selected][0],parent_comment,
                                                                        all_string_comments[comment_selected+1][0],seq_1_comment
                                                                        ))
                        break

                    #print(starting_nodes,all_ids)
                    if set(starting_nodes) == set(all_ids):
                        logging.info('No valid conversations found')
                        break

                num_pairs_created += 1
        if MAXIMUM_CHAIN_DEPTH == len(comment_chain):
            return
        for child in in_root_node.children:
            write_comment_chains(child, text_output_stream, num_dialogues_created, comment_chain)
    except RuntimeError as exc:
        print(in_previous_context)
        raise

def build_chain(reddit_comments_file):

    document_root = CommentTreeNode(0,None)
    all_nodes = {}

    with bz2.BZ2File(reddit_comments_file,'r') as rd:
        for line in tqdm(rd,total=get_num_lines(reddit_comments_file)):
            comment = json.loads(line)
            comment_id, parent_id, body = (
                comment['id'],
                comment.get('parent_id', None),
                comment['body']
            )
            parent_id = parent_id.partition('_')[2] if parent_id else None
            comment_node = CommentTreeNode(comment_id, body)
            all_nodes[comment_id] = comment_node
            if not parent_id:
                parent_node = document_root
            elif not parent_id in all_nodes:
                parent_node = CommentTreeNode(parent_id, '__CONTENT_MISSING__')
                document_root.adopt_child(parent_node)
                all_nodes[parent_id] = parent_node
            else:
                parent_node = all_nodes[parent_id]
            parent_node.adopt_child(comment_node)

    return document_root


def sample_reddit():
    with open('../extra/reddit_all.txt') as f, open('../corpra/reddit.txt', 'w') as wf:
        samples = random.sample(list(csv.reader(f, delimiter='\t')), 200)
        for sample in samples:
            wf.write('\t'.join([sample[2], sample[6]]) + '\n')



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Reddit conversation loader (Based on Igor\'s one)')
    parser.add_argument('--reddit_log_file','-r',help='Path to the reddit log file',required=True)
    parser.add_argument('--output_file','-o',help='path to the output file',required=True)

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    comment_tree_root = build_chain(args.reddit_log_file)

    num_dialogues_created = 0

    with open(args.output_file,'w') as OUTPUT_WRITER:
        stats = 0
        write_comment_chains(comment_tree_root, OUTPUT_WRITER,num_dialogues_created)



