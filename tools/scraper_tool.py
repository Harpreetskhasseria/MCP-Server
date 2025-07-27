from pydantic import BaseModel, Field
from typing import Dict, Type
import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from crewai.tools import BaseTool

# Output directory
OUTPUT_DIR = Path("regulatory_outputs/site_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Windows-specific fix
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Input schema
class ScraperInput(BaseModel):
    url: str = Field(..., description="The URL of the website to scrape")

# Tool class
class ScraperTool(BaseTool):
    name: str = "scraper_tool"
    description: str = "Scrapes raw HTML content from the provided URL and saves it to a file"
    args_schema: Type[BaseModel] = ScraperInput

    def _run(self, url: str) -> Dict:
        async def fetch_html(target_url: str) -> str:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(target_url, timeout=120_000)
                    await page.wait_for_selector("main", timeout=15_000)
                    await page.wait_for_load_state("networkidle")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(3000)
                    html = await page.content()
                    await browser.close()
                    return html
            except Exception as e:
                return f"<html><body><h1>Error scraping {target_url}</h1><p>{str(e)}</p></body></html>"

        html_content = asyncio.run(fetch_html(url))

        print("📦 ScraperTool: HTML length =", len(html_content), flush=True)
        print("🔍 HTML preview:", repr(html_content[:300]), flush=True)

        domain = urlparse(url).netloc.replace('.', '_')
        output_path = OUTPUT_DIR / f"{domain}_scraped.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ Scraped content saved to {output_path}", flush=True)

        return {
            "url": url,
            "scraped_file": str(output_path)
        }

# Instantiate
scraper_tool = ScraperTool()
