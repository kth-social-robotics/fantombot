import csv
import json
import os
import shutil
from collections import defaultdict
from glob import glob


def de_dup(f, delimiter="\t"):
    for line in f:
        yield delimiter.join(field for field in line.split(delimiter) if field)


def build_task(force=False):
    files = list(glob("../corpra/*.txt"))

    dataset_len = None
    corpora = {}

    for file_path in files:
        with open(file_path) as f:
            lines = list(csv.reader(de_dup(f), delimiter="\t"))
            if not dataset_len:
                dataset_len = len(lines)
            else:
                assert dataset_len == len(lines), file_path
            corpora[file_path] = lines

    annotation_data = defaultdict(list)

    n = 0
    for i in range(dataset_len):
        for dataset_name in files:
            assert len(corpora[dataset_name][i]) == 2, (
                corpora[dataset_name][i],
                dataset_name,
            )

            assert "\t" not in str(corpora[dataset_name][i]), (
                str(corpora[dataset_name][i]),
                dataset_name,
            )
            annotation_data[n // 105].append(
                {
                    "user_utterance": corpora[dataset_name][i][0],
                    "system_utterance": corpora[dataset_name][i][1],
                    "dataset_name": dataset_name,
                    "row_in_corpora": i,
                    "done": False,
                    "date": None,
                    "likely_user_utterance": None,
                    "coherent_system_utterance": None,
                    "interesting_system_utterance": None,
                    "continue_system_utterance": None,
                }
            )
            n += 1
    with open("annotations_data.json", "w") as f:
        json.dump(annotation_data, f)

    if force or not os.path.isfile("annotations_data_results.json"):
        shutil.copy("annotations_data.json", "annotations_data_results.json")


build_task()
