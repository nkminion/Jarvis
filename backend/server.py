from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from classifier import classify_intent, extract_parameters
from weather import get_weather_forecast
from llm import ask_bot
from core.handler import handler

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    text: str

@app.post("/process")
def process_text(data: UserInput):
    text = data.text
    intent, score = classify_intent(text)
    params = extract_parameters(text, intent)

    if intent == 'get_weather':
        location = params['location']
        date = params['date']
        time_ = params['time']
        params["forecast"] = get_weather_forecast(location, date, time_)
    elif intent == 'club_info':
        params['info'] = ask_bot(text)
    elif intent == 'general_question':
        result = handler(text)
        params["answer"] = result.get("answer", "")
        params["sources"] = result.get("sources", "")        
    return {
        "intent": intent,
        "score": score,
        "params": params
    }



