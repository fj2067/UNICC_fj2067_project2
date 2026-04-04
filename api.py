from fastapi import FastAPI
from pydantic import BaseModel

# This starts the web service
app = FastAPI()

# This defines what the input looks like
class AgentSubmission(BaseModel):
    agent_name: str
    agent_type: str
    risk_level: str
    prompt: str

# This is the endpoint — the drive-through window
# When someone sends a POST request to /evaluate
# this function runs and returns the verdict
@app.post("/evaluate")
def evaluate_agent(submission: AgentSubmission):
    
    # This calls Feruza's existing orchestrator
    result = orchestrator.run(submission)
    
    # This sends the JSON verdict back to whoever asked
    return result
