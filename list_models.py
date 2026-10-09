from dotenv import load_dotenv
from groq import Groq
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

for m in sorted(client.models.list().data, key=lambda m: m.id):
    print(m.id)