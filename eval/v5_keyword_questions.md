33 questions, k=6

| configuration | hit@6 | MRR | ms/query |
|----------|------------|-----------|--------------||---------------||----------------||---------------------|
| dense only | 0.97 | 0.76 | 22 |
| BM25 only | 0.91 | 0.69 | 18 |
| hybrid (RRF) | 0.94 | 0.85 | 44 |
| dense + rerank | 1.00 | 0.94 | 827 |
| hybrid + rerank | 1.00 | 0.91 | 955 |

Rank of first correct result per question (- = miss):

| question | dense only | BM25 only | hybrid (RRF) | dense + rerank | hybrid + rerank |
|---|---|---|---|---|---|
| What does the speaker say about God-given talents? | 1 | 1 | 1 | 1 | 1 |
| How tall is the speaker? | 2 | - | 4 | 1 | 1 |
| How does the class help students figure out their  | 1 | 1 | 1 | 1 | 1 |
| What is the chicken doing in the video? | 1 | 1 | 1 | 1 | 1 |
| What technologies are used for X-ray image classif | 1 | 1 | 1 | 1 | 1 |
| What projects are described in the CV? | 4 | 4 | - | 1 | 2 |
| Why is it dangerous to open a serialized model fil | 3 | 1 | 1 | 1 | 1 |
| How many flaws are deliberately built into the sta | 1 | 3 | 1 | 2 | 2 |
| Why do invalid request bodies get a different HTTP | 2 | 2 | 2 | 1 | 1 |
| What makes a Docker image smaller when the build i | 1 | 1 | 1 | 1 | 1 |
| What security benefit comes from not running the c | 3 | 1 | 1 | 2 | 3 |
| How can I verify that the exported portable model  | 1 | 4 | 2 | 2 | 2 |
| What minimum test coverage makes the test run fail | 1 | 2 | 1 | 1 | 1 |
| Which pieces of information must appear in every J | 1 | 1 | 1 | 1 | 1 |
| How do I follow one request through several servic | 1 | 1 | 1 | 1 | 1 |
| Why does the curl command behave strangely in Wind | 1 | 1 | 1 | 1 | 1 |
| Where should files live on Windows with WSL to kee | 1 | 1 | 1 | 1 | 1 |
| How do I make sure a teammate gets exactly the sam | 3 | 2 | 1 | 1 | 1 |
| What goes wrong if the preprocessing is not saved  | 2 | 1 | 1 | 1 | 1 |
| Which file format lets me train in one framework a | 4 | 1 | 2 | 1 | 1 |
| Which projects in the CV involve medical image mod | 3 | 1 | 1 | 1 | 1 |
| At what point in a serving app's life should the m | 1 | 3 | 1 | 1 | 1 |
| What is the name of the student the professor call | 1 | - | 4 | 1 | 1 |
| What reasons do the students give when asked what  | 1 | 4 | 1 | 1 | 1 |
| Why does the professor demand to know why nobody o | 1 | 2 | 1 | 1 | 1 |
| What does the professor say is wrong with staying  | 1 | 2 | 1 | 1 | 1 |
| Which lecture is about speaking up when something  | 1 | 2 | 1 | 1 | 1 |
| Which lecture is about discovering your natural ta | 1 | 2 | 1 | 1 | 1 |
| Which animals are around the campfire in the carto | 1 | 1 | 1 | 1 | 1 |
| Which picture has a gentube watermark on it? | - | 1 | 1 | 1 | 1 |
| What does the term opset mean for ONNX? | 2 | 1 | 1 | 1 | 1 |
| What does DictVectorizer do? | 3 | - | - | 2 | 3 |
| What is the purpose of the X-Request-ID header? | 1 | 1 | 1 | 1 | 1 |