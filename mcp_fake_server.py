from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# Define your fake tools
TOOLS = {
    "echo": {"input_schema": {"type": "string"}, "description": "Returns the input as-is."},
    "uppercase": {"input_schema": {"type": "string"}, "description": "Returns input in uppercase."},
    "reverse": {"input_schema": {"type": "string"}, "description": "Returns input reversed."}
}

class ToolCall(BaseModel):
    tool: str
    input: str

@app.get("/tools/list")
def list_tools():
    return list(TOOLS.keys())

@app.get("/tools/spec")
def get_tool_spec(tool: str):
    if tool in TOOLS:
        return TOOLS[tool]
    return {"error": "Tool not found"}

@app.post("/tools/call")
def call_tool(call: ToolCall):
    if call.tool == "echo":
        return {"output": call.input}
    elif call.tool == "uppercase":
        return {"output": call.input.upper()}
    elif call.tool == "reverse":
        return {"output": call.input[::-1]}
    else:
        return {"error": "Tool not found"}
