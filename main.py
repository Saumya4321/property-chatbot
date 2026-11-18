from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ask import ask

app = FastAPI()


class Question(BaseModel):
    message: str


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/chat")
def chat(q: Question):
    answer, model = ask(q.message)
    return {"answer": answer, "model": model}