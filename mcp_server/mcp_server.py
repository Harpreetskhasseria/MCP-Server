from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import importlib.util
import os
import inspect
from crewai.tools import BaseTool

TOOLS_PATH = "C:/Users/hp/Documents/MCP Server/tools"  # Path to your tools
app = FastAPI()
loaded_tools = {}

# Load all tools from TOOLS_PATH
def load_tools():
    global loaded_tools
    loaded_tools = {}

    for filename in os.listdir(TOOLS_PATH):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            file_path = os.path.join(TOOLS_PATH, filename)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for instances of BaseTool (already instantiated)
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, BaseTool):
                    loaded_tools[obj.name] = obj

# Initial load
load_tools()

@app.get("/tools/list")
def list_tools() -> List[str]:
    return list(loaded_tools.keys())

@app.get("/tools/spec")
def tool_spec(tool: str = Query(..., description="Tool name")):
    if tool not in loaded_tools:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool_obj = loaded_tools[tool]
    schema = tool_obj.args_schema
    args_fields = {}

    for field_name, field in schema.model_fields.items():  # Pydantic v2
        field_type = str(field.annotation.__name__) if hasattr(field.annotation, "__name__") else str(field.annotation)
        args_fields[field_name] = {
            "type": field_type,
            "description": field.description or ""
        }

    return {
        "name": tool_obj.name,
        "description": tool_obj.description,
        "args_schema": args_fields
    }

class ToolCall(BaseModel):
    tool: str
    input: Dict[str, Any]

@app.post("/tools/call")
def call_tool(body: ToolCall):
    if body.tool not in loaded_tools:
        raise HTTPException(status_code=404, detail="Tool not found")

    tool_obj = loaded_tools[body.tool]

    try:
        result = tool_obj.run(**body.input)
        return {"output": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
