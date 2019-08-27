import json
import numpy as np
import pandas as pd

with open("annotations_data_results.json") as f:
    a = json.load(f)

stuff = []
for participant, y in a.items():
    for x in y:
        x.update({"participant": participant})
        stuff.append(x)

df = pd.DataFrame(stuff)

df["coherent_system_utterance"] = df["coherent_system_utterance"].replace(-1, np.nan)
df["interesting_system_utterance"] = df["interesting_system_utterance"].replace(
    -1, np.nan
)
df["continue_system_utterance"] = df["continue_system_utterance"].replace(-1, np.nan)


df["dataset_name"] = df["dataset_name"].replace("../corpra/amazon_alexa.txt", "alexa")
df["dataset_name"] = df["dataset_name"].replace("../corpra/BNC.txt", "bnc")
df["dataset_name"] = df["dataset_name"].replace(
    "../corpra/edina_utterances.txt", "edina"
)
df["dataset_name"] = df["dataset_name"].replace(
    "../corpra/os_selected.txt", "open_subtitles"
)
df["dataset_name"] = df["dataset_name"].replace("../corpra/reddit.txt", "reddit")
df["dataset_name"] = df["dataset_name"].replace(
    "../corpra/switchboard_clean.txt", "switchboard"
)
df["dataset_name"] = df["dataset_name"].replace(
    "../corpra/tweets-cleaned.txt", "twitter"
)

grouped_by_dataset = df.groupby("dataset_name")

print("\n\nlikely_user_utterance")
print(grouped_by_dataset["likely_user_utterance"].describe())

print("\n\ncoherent_system_utterance")
print(grouped_by_dataset["coherent_system_utterance"].describe())

print("\n\ninteresting_system_utterance")
print(grouped_by_dataset["interesting_system_utterance"].describe())

print("\n\ncontinue_system_utterance")
print(grouped_by_dataset["continue_system_utterance"].describe())

df.to_csv("dataframe.csv")