from typing import Literal
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ask import ask

app = FastAPI()


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Question(BaseModel):
    message: str
    history: list[Message] = []


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/chat")
def chat(q: Question):
    history = [m.model_dump() for m in q.history[-6:]]
    answer, model = ask(q.message, history)
    return {"answer": answer, "model": model}