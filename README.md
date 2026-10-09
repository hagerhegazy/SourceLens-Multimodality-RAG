# SourceLens

Ask questions across your **PDFs, videos and images** and get answers with **evidence**: the page, the video frame and the timestamp each claim came from. If the answer is not in your files, it says so instead of guessing.

<!-- add a screenshot: ![SourceLens](docs/screenshot.png) -->

## What it does
- **PDFs** are split into overlapping chunks.
- **Videos** (files or links) are transcribed with Whisper; frames are described with BLIP and read with OCR (EasyOCR), and everything is merged by time.
- **Images** get a BLIP caption plus OCR text.
- **Questions** use hybrid search (meaning + keywords), a cross-encoder reranker, and an LLM that must cite its sources.
- A web UI (Gradio, custom dark-blue and yellow theme) shows the answer, the evidence pictures and clickable timestamps, and lets you remove sources.

## How it works
```
PDF ----> text chunks ------------------------------+
Video --> Whisper speech + BLIP frames + OCR text --+--> embeddings --> Chroma index
Image --> BLIP caption + OCR text -------------------+

Question --> dense search + BM25 --> rank fusion --> cross-encoder rerank --> LLM (Groq) --> answer + citations
```

## Results
Measured on 36 hand-written questions over ~15 sources (PDFs, lectures, a cartoon, a coding lesson). "hit@6": a correct source is in the top 6. "MRR": how near the top it is.

| retrieval setup | hit@6 | MRR |
|---|---|---|
| dense embeddings only | 0.97 | 0.74 |
| BM25 keywords only | 0.86 | 0.69 |
| hybrid (dense + BM25) | 0.89 | 0.78 |
| dense + reranker | 0.97 | 0.90 |
| **hybrid + reranker (default)** | **1.00** | **0.91** |

Answer check on a sample of 12 answerable questions: 12/12 answered, 12/12 cited a correct source, 11/12 judged fully supported by the retrieved text (the judge is the same model that writes the answers, so treat this as a rough guide). All 3 unanswerable questions got "Not found".


## Run it
Needs a free [Groq](https://console.groq.com) API key.

```bash
cp .env.example .env        # then put your key in .env
pip install -r requirements.txt
python app.py               # open http://127.0.0.1:7860
```

With Docker (the first build downloads PyTorch and is slow):
```bash
docker compose up --build   # open http://localhost:7860
```
The first question downloads the models and is slow. Command line: `python main.py ingest <file or link>` and `python main.py ask "question"`.

## Project layout
```
app.py            web UI (Gradio)               main.py            command line
pipeline.py       ingest / remove a source
ingest_pdf.py  ingest_video.py  ingest_audio.py  ingest_image.py  ingest_url.py
ocr.py  merge.py  store.py  retrieval.py  query.py  config.py
eval.py           retrieval evaluation          answer_eval.py     answer evaluation
eval/             saved results of every experiment
```

## Limitations
- The test set is small and written by me; results show it works on this data, not that it is perfect.
- Embeddings are English-only. Processing runs on CPU, so long videos are slow.
- Link downloads depend on the platform (YouTube also needs Deno installed); upload the file if a link fails.
- The same content in two files is not detected as a duplicate.
