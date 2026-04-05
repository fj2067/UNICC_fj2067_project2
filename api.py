from fastapi import FastAPI
from pydantic import BaseModel
from council.orchestrator import run_council

app = FastAPI()

class AgentSubmission(BaseModel):
    agent_name: str
    agent_type: str
    risk_level: str
    prompt: str

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/evaluate")
def evaluate_agent(submission: AgentSubmission):
    result = run_council(
        payload=submission.prompt,
        metadata={"agent_name": submission.agent_name, "agent_type": submission.agent_type},
        input_id=submission.agent_name
    )
    return result
