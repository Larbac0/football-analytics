from fastapi import FastAPI, BackgroundTasks
from run_etl import run
import logging

log = logging.getLogger(__name__)
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/run-etl/all")
async def trigger_etl_all(background_tasks: BackgroundTasks):
    for league in ["PL", "BSA", "CL"]:
        background_tasks.add_task(run, competition=league, days_back=7)
    return {"status": "started", "leagues": ["PL", "BSA", "CL"]}

@app.post("/run-etl/{competition}")
async def trigger_etl(competition: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(run, competition=competition, days_back=7)
    return {"status": "started", "competition": competition}
