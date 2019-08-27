from collections import namedtuple
import xml.etree.ElementTree as ET
import os
import random
import re
import copy
import numpy as np
"""Represents all of the info about a single word occurrence"""
#Dataset downloaded http://ota.ox.ac.uk/desc/2554
Stc = namedtuple('Stc', ['who', 'stc'])
pairs = []
current_pair = [] 
 
class BNCParser(object):
	"""A parser for British National Corpus (BNC) files"""
	def __init__(self, parser=None):
		if parser is None:
			parser = ET.XMLParser(encoding = 'utf-8')
		self.parser =  parser
 
	def parse(self, filename):
		tree = ET.parse(filename, self.parser)
		root = tree.getroot()
		stc = "" 
		for neighbour in root.iter('*'):
			if neighbour.tag == 's':
				#print stc
				yield Stc(neighbour.attrib['n'], stc)
				stc = ""
			elif neighbour.tag == 'w':
				stc += neighbour.text + " "
			elif neighbour.tag == 'c':
				stc = stc[:-1] + neighbour.text + " "

folders = []
class BNCParserFolder(object):
	def __init__(self, parser=None):
		if parser is None:
			parser = ET.XMLParser(encoding = 'utf-8')
		self.parser =  parser

	def parse(self, filename):
		tree = ET.parse(filename, self.parser)
		root = tree.getroot()
		for neighbour in root.iter('*'):
			if neighbour.tag == 'stext' and filename not in folders:
				print filename
				folders.append(filename)

path = './2554/download/Texts/'
for x in os.listdir(path):
	for y in os.listdir(path+x):
		for file in os.listdir(path+x+'/'+y+'/'):
			#print path+x+'/'+y+'/'+file
			source = path+x+'/'+y+'/'+file
			parser = BNCParserFolder()
			parser.parse(source)

print len(folders)
for source in folders:
	user = True
	parser = BNCParser()
	stc = ""
	p = parser.parse(source)
	who = 0
	for item in p:
		if stc == '':
			stc =  item[1]
		elif who == item[0]:
			stc +=  " " + item[1]
		if who != item[0] :
			if user:
				user = False
				current_pair = []
				current_pair.append(" ".join(stc.split()).lower())
			else:
				current_pair.append(" ".join(stc.split()).lower())
				pairs.append(current_pair)
				print who, item[0], current_pair
				current_pair = []
				user = True
			stc = ""
		who = item[0]

# filter on wordcount > 5 < 10
filtered_pairs = []
for pair in pairs:
	if len(pair[0].split()) < 5 or '?' not in pair[0].split()[-1]:
		continue
	if len(pair[1].split()) < 5 or '.' not in pair[1].split()[-1]:
		continue
	if len(pair[0].split()) > 10 or '?' not in pair[0].split()[-1]:
		continue
	if len(pair[1].split()) > 10 or '.' not in pair[1].split()[-1] :
		continue
	filtered_pairs.append(pair)

# extract 200 random pairs
print len(filtered_pairs)

random_pairs = []
while len(random_pairs) < 200:
	pair = random.choice(filtered_pairs)
	if pair not in random_pairs:
		random_pairs.append(pair)

with open("BNC.txt", "w") as f:
	for pair in random_pairs:
		f.write("\t\t".join(pair).encode('utf-8'))
		f.write("\n")
