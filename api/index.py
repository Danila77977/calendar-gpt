import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from pydantic import BaseModel
from calendar_agent import run_agent

app = FastAPI(
    title="Calendar-GPT API",
    description="Получает слоты и создаёт события",
    version="1.0"
)

class SlotsRequest(BaseModel):
    date: str

class EventRequest(BaseModel):
    start: str
    end:   str
    email: str

@app.post("/get_free_slots")
async def get_free_slots_endpoint(body: SlotsRequest):
    # run_agent вернёт строку с JSON-массивом слотов
    return {"slots": run_agent(f"Покажи свободные слоты на {body.date}")}

@app.post("/create_event")
async def create_event_endpoint(body: EventRequest):
    return {"confirmation": run_agent(
        f"Забронируй встречу {body.start} до {body.end} с {body.email}"
    )}
