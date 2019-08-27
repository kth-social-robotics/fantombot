import random
import re

cleaned_dialog_tuples = []
with open("tweets.txt", "r") as file:
	for line in file:
		triple = line.strip().split("\t")

		# Excluding deleted tweets (called none) and errors in formatting resulting in triples != 3
		if "none" in triple or len(triple) != 3:
			continue
		
		# Randomly decide if the extracted tuple is index 0 and 1 or 1 and 2
		utt1_index = random.randint(0, 1)
		utt2_index = utt1_index + 1

		# Remove @userids from data
		utt1 = triple[utt1_index]
		utt2 = triple[utt2_index]
		if utt1[0] == "@":
			utt1 = " ".join(utt1.split()[1:])
		if utt2[0] == "@":
			utt2 = " ".join(utt2.split()[1:])
		cleaned_dialog_tuples.append(utt1 + "\t" + utt2 + "\n")
		

f = open("tweets-cleaned.txt", "w")
for dia_tuple in random.sample(cleaned_dialog_tuples, 200):
	# Final cleaning - removal of smileys in htmlcode
	f.write(re.sub("&lt;3|&lt;", "", dia_tuple))
f.close()