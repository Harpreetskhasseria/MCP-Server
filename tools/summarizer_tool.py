# summarizer_tool.py

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Type
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import os

# Load environment variables
load_dotenv("C:/Users/hp/Documents/Agent Router Tools/.env")

# Output directory
OUTPUT_DIR = Path("regulatory_outputs/site_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Input schema
class SummarizerInput(BaseModel):
    text: str | None = Field(None, description="The raw text to summarize")
    extracted_text: str | None = Field(None, description="Alternative to 'text' if provided by extractor")
    source_url: str | None = Field(None, description="The original source URL of the content")
    url: str | None = Field(None, description="Alternative to 'source_url'")

# Tool class
class SummarizerTool(BaseTool):
    name: str = "summarizer_tool"
    description: str = "Summarizes regulatory text with compliance-specific focus for large banks like Wells Fargo"
    args_schema: Type[BaseModel] = SummarizerInput

    def _run(self, text: str = None, extracted_text: str = None, source_url: str = None, url: str = None) -> Dict:
        # Handle flexible input variants
        if text and source_url:
            content = text
            final_url = source_url
        elif extracted_text and url:
            content = extracted_text
            final_url = url
        else:
            raise ValueError("❌ Input must include ('text' + 'source_url') or ('extracted_text' + 'url')")

        # Prompt for GPT
        prompt = f"""
You are a regulatory analyst focused on large global financial institutions such as Wells Fargo.

Summarize the following content from a regulatory update. Your summary should highlight:

1. Key regulatory developments or announcements.
2. Implications or potential impact on large banks like Wells Fargo or their global peers.
3. Any new obligations, risk areas, or disclosures mentioned.

Respond in 2–4 sentences. Be precise and compliance-focused.

Content:
{content}
"""

        # Run OpenAI call
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()

        # Save summary to file
        domain = urlparse(final_url).netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = OUTPUT_DIR / f"{domain}_summary_{timestamp}.txt"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)

        print(f"✅ Saved summary to: {summary_file}")

        return {
            "source_url": final_url,
            "summary": summary,
            "summary_file": str(summary_file)
        }

# Tool instance (needed for MCP server discovery)
summarizer_tool = SummarizerTool()
