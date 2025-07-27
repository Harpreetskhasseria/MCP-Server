import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from urllib.parse import urlparse
from datetime import datetime
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from typing import Dict, Type


# Load environment variables
load_dotenv("C:/Users/hp/Documents/Agent Router Tools/.env")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Output directory
OUTPUT_DIR = Path("regulatory_outputs/site_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class LLMExclusionInput(BaseModel):
    url: str = Field(..., description="URL of the regulator site")
    extracted_file: str = Field(..., description="Path to the CSV file with extracted data")


class LLMExclusionTool(BaseTool):
    name: str = "llm_exclusion_tool"
    description: str = "Uses an LLM to classify regulatory updates as relevant or excluded for compliance."
    args_schema: Type[BaseModel] = LLMExclusionInput

    def _run(self, url: str, extracted_file: str) -> dict:
        file_path = Path(extracted_file)
        if not file_path.exists():
            raise FileNotFoundError(f"❌ Extracted file not found at: {file_path}")

        df = pd.read_csv(file_path)
        required_cols = {"topic", "additional_context", "regulator", "link"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"❌ Required columns missing: {required_cols - set(df.columns)}")

        df["Recommendation"] = ""
        df["Reason"] = ""

        print(f"🔍 Reviewing {len(df)} updates for exclusion...")

        for i, row in df.iterrows():
            topic = str(row.get("topic", "")).strip()
            context = str(row.get("additional_context", "")).strip()
            regulator = str(row.get("regulator", "")).strip()

            prompt = f"""
You are a compliance filtering assistant for a U.S. bank.

Given the topic, supporting context, and regulator source, decide whether this content is relevant for compliance monitoring.

Respond in JSON format like this:
{{
  "recommendation": "Include" or "Exclude",
  "reason": "short explanation"
}}

Topic: {topic[:300]}
Context: {context[:1000]}
Regulator: {regulator}
"""
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a compliance content classifier."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                content = response.choices[0].message.content.strip()
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                parsed = json.loads(content[json_start:json_end])
            except Exception as e:
                print(f"⚠️ Failed to parse LLM output: {e}")
                parsed = {
                    "recommendation": "Exclude",
                    "reason": f"⚠️ LLM error or invalid output: {str(e)}"
                }

            df.at[i, "Recommendation"] = parsed.get("recommendation", "Exclude")
            df.at[i, "Reason"] = parsed.get("reason", "No reason provided")

        # Format hyperlink
        df["Link"] = df["link"].apply(
            lambda x: f'=HYPERLINK("{x}", "Open Link")' if pd.notna(x) and str(x).startswith("http") else ""
        )
        df.drop(columns=["link"], inplace=True)

        # Add action column
        df["action"] = ""

        domain = urlparse(url).netloc.replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = OUTPUT_DIR / f"{domain}_llm_exclusion_checked_{timestamp}.xlsx"

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Exclusion Results")
            workbook = writer.book
            sheet = writer.sheets["Exclusion Results"]

            action_col_idx = df.columns.get_loc("action") + 1
            action_col_letter = get_column_letter(action_col_idx)

            dv = DataValidation(
                type="list",
                formula1='"summarize,custom prompt,no action"',
                allow_blank=True,
                showDropDown=False
            )
            dv.error = "Invalid input. Choose from summarize, custom prompt, or no action."
            dv.errorTitle = "Invalid Action"

            dv.add(f"{action_col_letter}2:{action_col_letter}101")
            sheet.add_data_validation(dv)

        print(f"✅ Exclusion results saved to: {output_path}")

        return {
            "url": url,
            "exclusion_file": str(output_path)
        }

llm_exclusion_tool = LLMExclusionTool()
