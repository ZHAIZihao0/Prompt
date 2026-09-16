from google import genai
from pydantic import BaseModel, Field, TypeAdapter
from typing import List, Optional
from google.genai import types
import json
import os
from pathlib import Path
from bs4 import BeautifulSoup


# Read JSON file
def read_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"File {filename} Not Found")
        return None


# Read footnote
def read_footnote(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            footnotes = []

            divs = [
                'div.article-section__table-footnotes',
                'div.c-article-table-footer',
                'div.tw-foot',
                'div.table-wrap-foot',
                'div[class*="footnote"]:not([class*="inline"])',
                'div[class*="footnotes"]',
                'div.inline-table__legend',
                'div.article-table-descriptions',
                'div.notes'
            ]

            containers = []
            for div in divs:
                containers.extend(soup.select(div))

            # Remove repeated footnote
            containers = list(dict.fromkeys(containers))

            for container in containers:
                items = container.find_all('li') + container.find_all('div', class_='fn')
                if items:
                    for item in items:
                        text = ' '.join(item.stripped_strings)
                        if text:
                            footnotes.append(text)
                else:
                    text = ' '.join(container.stripped_strings)
                    if text:
                        footnotes.append(text)

            # connect all footnote with space
            return ' '.join(footnotes)
    except FileNotFoundError:
        print(f"File {filename} Not Found")
        return ""


# Set output structure
class Value(BaseModel):
    number: str = Field(description="The numerical value as string")
    type: str = Field(description="The data type of the numerical value (count, percentage, mean, etc.)")
    unit: str = Field(description="The unit of measurement")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class Datacell(BaseModel):
    data_cell: str = Field(description="The value in the data cell")
    serial_number: str = Field(description="Serial number of the data cell")
    value1: Value = Field(default=None, description="First numerical value")
    value2: Value = Field(default=None, description="Second numerical value")
    value3: Value = Field(default=None, description="Third numerical value")
    value4: Value = Field(default=None, description="Fourth numerical value")
    value5: Value = Field(default=None, description="Fifth numerical value")
    value6: Value = Field(default=None, description="Sixth numerical value")
    value7: Value = Field(default=None, description="Seventh numerical value")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


def process_JSON_table(html_filepath, json_filepath):
    # Input JSON table
    input_table = read_json(json_filepath)
    # Input HTML table Footnote
    footnote = read_footnote(html_filepath)

    # List all included unit code and data type
    unit_mapping = {
        "Fahrenheit": "C44277",  # Degree Fahrenheit
        "IU/L": "C67376",  # International Unit per Liter
        "μIU/mL": "C67376",  # International Unit per Liter
        "IU/mL": "C67377",  # International Unit per Milliliter
        "L/L": "C105495",  # Liter Per Liter
        "U/L": "C67456",  # Unit per Liter
        "μU/mL": "C67456",  # Unit per Liter
        "U/day": "C67464",  # Unit per 24 Hours
        "units/day": "C67464",  # Unit per 24 Hours
        "U/kg": "C67465",  # Unit per Kilogram
        "U/mL": "C77607",  # Unit per Milliliter
        "beat/min": "C49673",  # Beats per Minute
        "beats/min": "C49673",  # Beats per Minute
        "bpm": "C49673",  # Beats per Minute
        "breaths/min": "C49674",  # Breaths per Minute
        "cm": "C49668",  # Centimeter
        "cm/s": "C102406",  # Centimeter per Second
        "cm2": "C48460",  # Square Centimeter
        "days": "C25301",  # Day
        "g": "C48155",  # Gram
        "g/L": "C42576",  # Kilogram per Cubic Meter
        "mg/mL": "C42576",  # Kilogram per Cubic Meter
        "g/dL": "C64783",  # Gram per Deciliter
        "g/day": "C67372",  # Gram per 24 Hours
        "g/gCr": "C105485",  # Gram Per Gram of Creatinine
        "g/m2": "C67282",  # Gram per Square Meter
        "g/mol": "C73721",  # Gram per Mole
        "mg/mmol": "C73721",  # Gram per Mole
        "inches": "C48500",  # Inch
        "kg": "C28252",  # Kilogram
        "kg/m2": "C49671",  # Kilogram per Square Meter
        "m/s": "C42571",  # Meter per Second
        "mIU/L": "C67405",  # Microinternational Unit per Milliliter
        "mL/m2": "C73761",  # Milliliter per Square Meter
        "mL/min": "C64777",  # Milliliter per Minute
        "mL/min/1.73m2": "C67412",  # Milliliter per Minute per 1.73 m2 of Body Surface Area
        "mg": "C28253",  # Milligram
        "mg/24 h": "C67399",  # Milligram per 24 Hours
        "mg/24h": "C67399",  # Milligram per 24 Hours
        "mg/day": "C67399",  # Milligram per 24 Hours
        "mg/L": "C64572",  # Microgram per Milliliter
        "μg/mL": "C64572",  # Microgram per Milliliter
        "mg/dL": "C67015",  # Milligram per Deciliter
        "mg/g": "C69104",  # Gram per Kilogram
        "μg/mg": "C69104",  # Gram per Kilogram
        "mg/gCr": "C105502",  # Milligram Per Gram of Creatinine
        "mg/mol": "C120843",  # Milligram per Mole
        "mm": "C28251",  # Millimeter
        "mmHg": "C49670",  # Millimeter of Mercury
        "mmol": "C48513",  # Millimole
        "mmol/L": "C64387",  # Millimole per Liter
        "mmol/mol": "C111253",  # Millimole per Mole
        "months": "C29846",  # Month
        "ms": "C41140",  # Millisecond
        "ng/L": "C67327",  # Nanogram per Liter
        "pg/mL": "C67327",  # Nanogram per Liter
        "ng/mL": "C67306",  # Microgram per Liter
        "nmol/L": "C67432",  # Nanomole per Liter
        "percentage": "C48570",  # Percent Unit
        "pmol/L": "C67434",  # Picomole per Liter
        "pounds": "C48531",  # Pound
        "uU/mL": "C67408",  # Microunit per Milliliter
        "umol/L": "C48508",  # Micromole per Liter
        "μmol/L": "C48508",  # Micromole per Liter
        "units": "C48579",  # International Unit
        "volume percentage": "C48571",  # Percent Volume per Volume
        "weeks": "C29844",  # Week
        "years": "C29848",  # Year
        "µS": "C154859",  # Microsiemens
        "μg/min": "C71211",  # Microgram per Minute
        "calendar years": "C210821",  # Year of Diagnosis
        "ratio": "C44256",  # Ratio
        "p value": "C44185",  # P-Value
        "ng/mLmin": "C85732",  # Minute Times Nanogram per Milliliter
        "test statistic": "C53235",  # Chi-Square Test
        "count": "Others",  # Count
        "unitless": "Others",  #
        "units/week": "Others",  #
    }

    type_mapping = ["count", "percentage", "interquartile range", "lower quartile", "upper quartile", "range_min",
                    "range_max",
                    "mean", "median", "p value", "ratio", "standard deviation", "test statistic", "total number"]
    datatype = json.dumps(type_mapping, ensure_ascii=False)

    # Prompt
    prompt = f"""<system>
You are a data extraction and semantic analysis specialist. Your task is to parse a baseline characteristics table stored as a JSON array, extract numerical data from each cell, infer their statistical types and units based on the associated row headers, column headers and footnotes, and map the units to standardized ontology codes from the NCI Thesaurus (OBO Edition).
</system>
A JSON file containing non-empty data cells extracted from a baseline characteristic table. Each object may have the following fields: 
“data_cell”: The value stored in data cell.
“row header”: The row headers associated with the data cell.
“column header”: The column headers associated with the data cell.
“serial_number”: A unique identifier.
<instructions>
Follow these steps sequentially and ensure the final output is strictly based on the reasoning process.
1. Extract numerical values: Analyze the “data_cell” and extract all distinct numeric values, split them into individual values, order the values sequentially as they appear in the “data_cell” and label them value1, value2, ..., valuen.
2. Infer the statistical type for each value: Use the combined context of the row headers, column headers and footnotes to determine what each value represents. For example, if headers contain "n (%)", the first value is "count", and the second is "percentage". If headers contain "mean (SD)", the first value is "mean", and the second is "standard deviation". After inferring the type, you MUST map it to one of the following standard type formats. If the inferred type cannot be mapped to any standard format, output as “Others”. Standard type formats: {datatype}
3. Infer the unit of measurement for each value: Infer the unit from the row headers, column headers text and footnotes. For example, kg, year. For counts/percentages without a physical unit, the unit is "count" or "percent". If the row and column headers do not contain any unit, attempt to infer from the table footnote. If still no unit can be inferred, assign the unit as "Others".
4. Map the Inferred Unit to NCIT code: There is an ontology list that maps the possible units in the table to their corresponding codes. For each inferred unit, map it to one of the following standard NCIT codes according to the list below. If the inferred unit cannot be matched to any code in the list, output as “Others”. Standard unit codes: {unit_mapping}
5. Generate the Output JSON: Process every object in the input JSON array. For each object, output a JSON object that verbatim includes:
“data_cell”: the original data_cell
“serial_number”: the original serial_number.
“value”: An array of objects, one per extracted number, each containing:
  “value”: An independent numerical value.
  “type”: inferred statistical type, or “Others” if not found.
  “unit”: the NCI Thesaurus code, or “Others” if not found.
Based on above analysis, generate a downloadable JSON file. The JSON output must correspond to analysis from above steps.
</instructions>
<input>
Process the JSON file:
{input_table}
The table footnote:
{footnote}
</input>
"""

    # Model and Parameter
    client = genai.Client(api_key="")  # Input API key

    print(f"Processing: {json_filepath}")
    adapter = TypeAdapter(List[Datacell])
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=adapter.json_schema(),
            temperature=0,
            top_p=0.95,
            max_output_tokens=65536,
            thinking_config=types.ThinkingConfig(
                # thinking_budget=24576,
                # include_thoughts=True
            )
        )
    )

    for candidate in response.candidates:
        print("Finish reason:", candidate.finish_reason)

    if hasattr(response, 'usage_metadata'):
        print("Input tokens length:", response.usage_metadata.prompt_token_count)
        print("Thinking tokens:", response.usage_metadata.thoughts_token_count)
        print(f"Output token length:", response.usage_metadata.candidates_token_count)
        print("Total tokens:", response.usage_metadata.total_token_count)

    # Process JSON output
    response_text = response.text

    if '```json' in response_text:
        json_text = response_text.split('```json')[1].split('```')[0].strip()
    elif '```' in response_text:
        json_text = response_text.split('```')[1].split('```')[0].strip()
    else:
        json_text = response_text

    # Get file name
    input_name = Path(json_filepath).stem
    output_name = f"{input_name}.json"

    # Save as JSON file
    output_dir = Path("")  # LLM output JSON filepath
    try:
        parsed = json.loads(json_text)
        output_path = output_dir / output_name
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)

        print(f"Output save as JSON file: {output_path}")

        return output_path
    except Exception as e:
        print(f"Error: {e}")
        print("Failed to Save JSON.")
        response_path = output_dir / "response.txt"
        with open(response_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
        return None


if __name__ == "__main__":
    # Input filepath
    html_folder_path = ''  # Input HTML filepath
    json_folder_path = ''  # Input JSON filepath

    json_files = [f for f in os.listdir(json_folder_path) if f.endswith('.json')]
    for json_file in json_files:
        filename = os.path.splitext(json_file)[0]
        html_file = filename + ".html"
        html_path = os.path.join(html_folder_path, html_file)
        json_path = os.path.join(json_folder_path, json_file)

        if os.path.exists(html_path):
            process_JSON_table(html_path, json_path)
            print(f"Finish: {json_file}")
        else:
            print(f"Warning: HTML file {html_file} not found.")
