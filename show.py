import sys
import store

data = store._col().get(where={"source": sys.argv[1]}, include=["documents", "metadatas"])
rows = sorted(zip(data["metadatas"], data["documents"]),
              key=lambda r: (r[0]["modality"], r[0]["location"]))
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
for m, d in rows:
    print(m["modality"], m["location"], "|", d[:limit])