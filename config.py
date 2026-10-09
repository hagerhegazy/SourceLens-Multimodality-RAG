import os
from dotenv import load_dotenv

load_dotenv(override=True)   # .env wins over any variable already set in the shell

DB_DIR = "store/chroma"
FRAMES_DIR = "store/frames"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
CAPTION_MODEL = "Salesforce/blip-image-captioning-base"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MIN_SCORE = float(os.getenv("MIN_SCORE", "-100"))   # filter is off until you tune it
CHUNK_WORDS = 200
CHUNK_OVERLAP = 40
FRAME_EVERY_SEC = 2
TOP_K = 6
SAMPLE_EVERY_SEC = 0.5     # how often we check for a scene change
SCENE_THRESHOLD = 0.35     # 0 = identical, 1 = completely different; lower = more frames kept
MIN_GAP_SEC = 1            # never caption more often than this
MAX_GAP_SEC = 10    
USE_OCR = os.getenv("USE_OCR", "1") == "1"
MERGE_FRAMES = os.getenv("MERGE_FRAMES", "1") == "1"
MIN_SPEECH_WORDS = 30     # below this a video counts as "no speech" and keeps its frame records
MAX_VISUALS = 3           # distinct frame descriptions folded into one speech chunk       # always caption at least this often, even with no change
OCR_CORNERS = os.getenv("OCR_CORNERS", "0") == "1"
MAX_VIDEO_SEC = 600      # refuse longer videos so ingestion stays quick
EVAL_ALIASES = {
    "lec.mp4": ["youtube_ALYUQ5X5Mvo.mp4"],
    "lec2.mp4": ["Instagram_DJHAi3PSyoo.mp4"],
}
SCREEN_RECORDS = os.getenv("SCREEN_RECORDS", "1") == "1"
OCR_LANGS = os.getenv("OCR_LANGS", "en").split(",")