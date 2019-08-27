import os
import random


path = "dialogues/"

# extract pairs
pairs = []
current_pair = []
for file in os.listdir(path):
	with open(path+file, "r") as f:
		user = True
		current_pair = []
		for line in f.readlines():
			if user:
				user = False
				current_pair.append(line.strip())
			else:
				current_pair.append(line.strip())
				pairs.append(current_pair)
				current_pair = []
				user = True

# filter on wordcount >= 5 <= 10
filtered_pairs = []
for pair in pairs:
	if len(pair[0].split()) <= 5:
		continue
	if len(pair[1].split()) <= 5:
		continue
	if len(pair[0].split()) >= 10:
		continue
	if len(pair[1].split()) >= 10:
		continue
	filtered_pairs.append(pair)


# extract 200 random pairs and write to edina_utterances.txt
random_pairs = []
while len(random_pairs) < 200:
	pair = random.choice(filtered_pairs)
	if pair not in random_pairs:
		random_pairs.append(pair)

with open("edina_utterances.txt", "w") as f:
	for pair in random_pairs:
		f.write("\t".join(pair))
		f.write("\n")