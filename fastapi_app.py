from fastapi import FastAPI
from pydantic import BaseModel
from calendar_agent import run_agent

app = FastAPI()

class SlotsRequest(BaseModel):
    date: str   # YYYY-MM-DD

class EventRequest(BaseModel):
    start: str  # ISO, например "2025-08-01T14:00:00+03:00"
    end: str    # ISO, например "2025-08-01T14:30:00+03:00"
    email: str

@app.post("/get_free_slots")
async def get_free_slots_endpoint(body: SlotsRequest):
    # вернёт JSON-список свободных слотов
    content = run_agent(f"Покажи свободные слоты на {body.date}")
    return {"slots": content}

@app.post("/create_event")
async def create_event_endpoint(body: EventRequest):
    # запланирует встречу и вернёт ссылку
    content = run_agent(
        f"Забронируй встречу {body.start} до {body.end} с {body.email}"
    )
    return {"confirmation": content}
