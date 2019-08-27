import pandas as pd
import progressbar


class DialogGenerator(object):
    @staticmethod
    def full_paths(df, show_progress, new_style):
        if show_progress:
            bar = progressbar.ProgressBar(max_value=len(df[df["parent_id"] == 0]))

        def recur(nid):
            results = []
            d = df[df["id"] == nid]
            partial_df = df[df["parent_id"] == nid]
            val = []

            if not d.empty:
                if new_style:
                    val.append(
                        {
                            "id": d.values[0][0],
                            "is_user_utterance": d.values[0][1],
                            "parent_id": d.values[0][2],
                            "text": d.values[0][3],
                        }
                    )
                else:
                    val.append(d.values[0][3])

            if partial_df.empty:
                return [val]

            root_counter = 1
            for index, row in partial_df.iterrows():
                if show_progress and nid == 0:
                    bar.update(root_counter)
                    root_counter += 1

                for r in recur(row["id"]):
                    results.append(val + r)
            return results

        return recur(0)
