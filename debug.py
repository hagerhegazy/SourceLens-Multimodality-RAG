import sys
import store
from retrieval import retrieve

print("Records in index:", store._col().count())
q = " ".join(sys.argv[1:])
for h in retrieve(q):
    print(f"{h['score']:.2f}", h["modality"], h["source"], h["location"], "|", h["content"][:80])