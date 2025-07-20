import os
import json
from difflib import SequenceMatcher


def normalize(t):
    return t.lower().strip()


def sim(a, b):
    return SequenceMatcher(None, a, b).ratio()


def compare(pred, gold):
    matched = 0
    used = set()
    for p in pred:
        for i, g in enumerate(gold):
            if i in used: continue
            if p['level'] == g['level'] and p['page'] == g['page']:
                if sim(p['text'], g['text']) >= 0.85:
                    matched += 1
                    used.add(i)
                    break
    return matched


def evaluate(pred_path, gold_path):
    pred = json.load(open(pred_path, encoding='utf-8')).get("outline", [])
    gold = json.load(open(gold_path, encoding='utf-8')).get("outline", [])

    precision = compare(pred, gold) / len(pred) if pred else 0
    recall = compare(pred, gold) / len(gold) if gold else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision+recall) else 0
    return precision, recall, f1


if __name__ == "__main__":
    pred_dir = "output"
    gold_dir = "ground_truth"
    scores = []

    for file in os.listdir(pred_dir):
        if file.endswith(".json"):
            pred_path = os.path.join(pred_dir, file)
            gold_path = os.path.join(gold_dir, file)
            if os.path.exists(gold_path):
                p, r, f = evaluate(pred_path, gold_path)
                scores.append((file, p, r, f))

    for fname, p, r, f in scores:
        print(f"{fname}: Precision={p:.2f}, Recall={r:.2f}, F1={f:.2f}")

    avg_f1 = sum(f for _, _, _, f in scores) / len(scores) if scores else 0
    print(f"\nAverage F1 Score: {avg_f1:.2f}")
