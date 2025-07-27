import traceback
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from typing import Dict, Type

# Output directory
OUTPUT_DIR = Path("regulatory_outputs/site_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Tags to remove
TAGS_TO_REMOVE = ["script", "style", "noscript", "footer", "header", "nav", "aside"]

# Input schema
class CleanerInput(BaseModel):
    url: str = Field(..., description="Original URL of the scraped site")
    scraped_file: str = Field(..., description="Path to the scraped HTML file on disk")

# Tool class
class CleanerTool(BaseTool):
    name: str = "cleaner_tool"
    description: str = "Cleans HTML file content by removing unnecessary tags and outputs cleaned file"
    args_schema: Type[BaseModel] = CleanerInput

    def _run(self, **kwargs) -> Dict:
        try:
            input = CleanerInput(**kwargs)
            url = input.url.strip('"')
            file_path = Path(input.scraped_file.strip('"'))

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            scraped_html = file_path.read_text(encoding="utf-8").strip()
            print(f"🔧 CleanerTool _run invoked for file: {file_path}", flush=True)
            print(f"URL: {url} | HTML length: {len(scraped_html)}", flush=True)

            if not scraped_html:
                raise ValueError("Received empty HTML from scraped file")

            soup = BeautifulSoup(scraped_html, "html.parser")
            for tag in TAGS_TO_REMOVE:
                for el in soup.find_all(tag):
                    el.decompose()
            for tag in soup.find_all():
                if not tag.get_text(strip=True) and tag.name not in ["br", "hr"]:
                    tag.decompose()

            cleaned_html = soup.prettify()
            domain = urlparse(url).netloc.replace(".", "_")
            output_path = OUTPUT_DIR / f"{domain}_cleaned.html"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned_html)

            print(f"✅ Cleaned HTML saved to: {output_path}", flush=True)

            return {
                "url": url,
                "cleaned_html": cleaned_html,
                "cleaned_file": str(output_path)
            }

        except Exception:
            print("❌ Error in CleanerTool:", flush=True)
            traceback.print_exc()
            raise

# Instantiate
cleaner_tool = CleanerTool()
