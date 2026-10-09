30 questions, k=6 (before OCR + frame/speech merge)

| configuration | hit@6 | MRR | ms/query |
|---|---|---|---|
| dense only | 0.93 | 0.67 | 21 |
| BM25 only | 0.83 | 0.67 | 18 |
| hybrid (RRF) | 0.90 | 0.78 | 47 |
| dense + rerank | 0.97 | 0.90 | 872 |
| hybrid + rerank | 0.93 | 0.84 | 954 |
| hybrid + rerank (30) | 0.97 | 0.88 | 1455 |