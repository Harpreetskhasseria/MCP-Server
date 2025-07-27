from pydantic import BaseModel, Field
from typing import Dict, Type
from crewai.tools import BaseTool

# Define the input schema
class DebugProxyInput(BaseModel):
    scraped_html: str = Field(..., description="The scraped HTML to inspect for debugging")

# Define the tool class
class DebugProxyTool(BaseTool):
    name: str = "debug_proxy_tool"
    description: str = "Logs the scraped HTML length and preview to help debug LangGraph tool handoffs"
    args_schema: Type[BaseModel] = DebugProxyInput

    def _run(self, scraped_html: str) -> Dict:
        print("🔍 [DebugProxyTool] HTML length:", len(scraped_html), flush=True)
        print("📄 [DebugProxyTool] HTML preview (first 300 chars):", repr(scraped_html[:300]), flush=True)
        return {"scraped_html": scraped_html}

# Instantiate the tool so MCP can discover it
debug_proxy_tool = DebugProxyTool()
