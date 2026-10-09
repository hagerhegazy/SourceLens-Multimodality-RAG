from collections import Counter
import store

data = store._col().get(include=["metadatas"])
counts = Counter((m["source"], m["modality"]) for m in data["metadatas"])
for (src, mod), n in sorted(counts.items()):
    print(f"{src:45} {mod:8} {n}")