import sys
from pipeline import ingest
from query import answer, cite

USAGE = "python main.py ingest <file or video link>   |   python main.py ask \"question\""

if len(sys.argv) < 3:
    sys.exit(USAGE)

cmd, arg = sys.argv[1], " ".join(sys.argv[2:])
if cmd == "ingest":
    try:
        path, n = ingest(arg)
    except ValueError as e:
        sys.exit(str(e))
    print(f"Indexed {n} records from {path}")
elif cmd == "ask":
    text, hits = answer(arg)
    print(text, "\n\nRetrieved:")
    for h in hits:
        print(" ", f"{h['score']:.2f}", cite(h), h["content"][:80])
else:
    sys.exit(USAGE)