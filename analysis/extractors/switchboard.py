#link to dataset https://catalog.ldc.upenn.edu/LDC97S62
import os
import random
import re
import copy
import numpy as np

path = "dialogues/"

# extract pairs
pairs = []
current_pair = []


for x in os.listdir(path):
	for file in os.listdir(path+x+'/'):
		with open(path+x+'/'+file, "r") as f:
			user = True
			current_pair = ['','']
			for line in f.readlines():
				if "A." in line or "B." in line:
					part , line = line.split(":",1)
					if "A." in part:
						if user:
							pairs.append(current_pair)
							current_pair = ['','']
							user = False
						current_pair[0] += line
					if "B." in part:
						current_pair[1] += line
						user = True
			pairs.append(current_pair)
			

# filter on wordcount > 5 < 10
filtered_pairs = []
original_pairs = [] 
remove = ['<','>','{','}','[',']',"-","+","#","(",")","/","\n"]

for pair in pairs:
	temp_pair = []
	for item in pair:
		if '[' in item and ',' in item and ']' in item and '*[[' not in item:
			item = ''
		#if item.count('{'):
		#	item = ''
		num = item.count('{')
		for i in range(num):					
			start = item.find('{')
			end = item.find('}')
		#	item = item[0:start] + item[start+2:] #to include {C and } parts				
			if end != -1:							#not to include {C and } parts
				item = item[0:start] + item[end+1:]					
		num = item.count('<')
		for i in range(num):					
			start = item.find('<')
			end = item.find('>')							
			item = item[0:start] + item[end+1:]
		num = item.count('*[[')
		for i in range(num):					
			start = item.find('*[[')
			end = item.find(']]')							
			item = item[0:start] + item[end+1:]
		for l in remove:
			item = item.replace(l, '')
		item = ' '.join(item.split())
		temp_pair.append(item)
	if len(temp_pair[0].split()) < 5 or temp_pair[0][-1] != '?' :
		continue
	if len(temp_pair[1].split()) < 5 or temp_pair[1][-1] == ',':
		continue
	if len(temp_pair[0].split()) > 10 or temp_pair[0][-1] != '?':
		continue
	if len(temp_pair[1].split()) > 10 or temp_pair[1][-1] == ',':
		continue
	filtered_pairs.append(temp_pair)
	original_pairs.append(pair)

# extract 200 random pairs
random_pairs_clean = []
random_pairs_orig = []
print (len(filtered_pairs))
rand_id = np.random.choice(len(filtered_pairs), 200,replace=False)

f = open("switchboard_original.txt", "w")
f1 = open("switchboard_clean.txt", "w")
for ids in rand_id:
	f.write(original_pairs[ids][0].replace('\n', '')+'\t\t\t'+original_pairs[ids][1].replace('\n', '')+'\n')
	f1.write(filtered_pairs[ids][0]+'\t\t\t'+filtered_pairs[ids][1]+'\n')

f.close()
f1.close()

