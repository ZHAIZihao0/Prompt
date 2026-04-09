from google import genai
from pydantic import BaseModel, Field, TypeAdapter
from typing import List, Optional
from google.genai import types
import json
import os
from pathlib import Path
from bs4 import BeautifulSoup


# Read file
def read_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {filename} Not Found")
        return ""


# Read table
def read_table(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            table = soup.find_all('table')
            return table
    except FileNotFoundError:
        print(f"File {filename} Not Found")
        return ""


# Set output JSON structure
class RowHeader(BaseModel):
    row_header_level_1: str = Field(description="First level row header", alias="row header level-1")
    row_header_level_2: Optional[str] = Field(None, description="Second level row header", alias="row header level-2")
    row_header_level_3: Optional[str] = Field(None, description="Third level row header", alias="row header level-3")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class ColumnHeader(BaseModel):
    column_header_level_1: str = Field(description="First level column header", alias="column header level-1")
    column_header_level_2: Optional[str] = Field(None, description="Second level column header",
                                                 alias="column header level-2")
    column_header_level_3: Optional[str] = Field(None, description="Third level column header",
                                                 alias="column header level-3")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


class TableCell(BaseModel):
    data_cell: str = Field(description="The value in the data cell", alias="data cell")
    row_header: RowHeader = Field(description="Row header information", alias="row header")
    column_header: ColumnHeader = Field(description="Column header information", alias="column header")
    serial_number: str = Field(description="Serial number of the data cell", alias="serial_number")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True


def process_html_table(table_file_path):
    # Example and Input table
    example_html = read_file("") #Example input filepath
    example_output = read_file("") #Example output filepath
    input_table = read_table(table_file_path)

    # Prompt
    prompt = f"""<system>
  You are a specialist in tabular data processing. There is a table in HTML format. The table consists of caption, column headers, row headers, data cells and footer. A data cell refers to any non-empty cell that is not a row header or a column header. Your task is to convert all data cells and their related row and column headers into a structured JSON format for sufficient subsequent analysis.
  </system>
  <instructions>
  Follow these steps sequentially and ensure the final output is strictly based on your reasoning process.
  1. Table Structure Analysis: Identify which rows serve as the column headers and which columns serve as the row headers. Pay attention to multi-level headers and merged cells.
  2. Data Cell Identification: Identify all cells that are non-empty and are not part of the row or column headers. These are to be considered data cells. For each data cell, extract the serial_number attribute from the td tag.
  3. Row and column headers association: For each data cell object, you need to identify the related row headers and column headers. When the headers of a data cell have multiple layers of structure, you need to divide the headers into different levels based on their priority. For example, "row header level-1", "column header level-2" and "row header level-3". You must process superscript elements according to the following criteria: RETAIN superscripts that represent mathematical notation, scientific units, or are integral parts of the header/data meaning. REMOVE superscripts that represent footnotes, references, or annotations. Examples: `a`, `b`, `c`, `*`, `†`, `‡` and similar annotation markers. Extract and output only the cleaned textual content after applying these rules.
  4. Output formatting: For each data cell object, verbatim output its value, row headers, column headers, serial_number in order. If a data cell has multiple row headers or multiple column headers, you need to output all headers related to this data cell. Based on above analysis, generate a downloadable JSON file. The JSON output must correspond to analysis from above steps.
  </instructions>
  <example>Example2.html is an input example,
  {example_html}
  and Example2Output.json is the corresponding output example.
  {example_output}
  </example>
  <table>
  Process the HTML table:
  {input_table}
  </table>
  """

    # Model and Parameter
    client = genai.Client(api_key="") #LLM API key

    print(f"Processing: {table_file_path}")
    adapter = TypeAdapter(List[TableCell])
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=adapter.json_schema(),
            temperature=0,
            top_p=0.95,
            max_output_tokens=65536,
            #thinking_config=types.ThinkingConfig(thinking_budget=0)
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

    # print(f"Response: {response_text}")
    # with open('response.txt', 'w', encoding='utf-8') as f:
    # f.write(response_text)

    if '```json' in response_text:
        json_text = response_text.split('```json')[1].split('```')[0].strip()
    elif '```' in response_text:
        json_text = response_text.split('```')[1].split('```')[0].strip()
    else:
        json_text = response_text

    # Get file name
    input_name = Path(table_file_path).stem
    output_name = f"{input_name}.json"

    # Save as JSON file
    output_dir = Path("") #Output JSON files folder path
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
    folder_path = '' #Input HTML tables folder path
    html_files = [f for f in os.listdir(folder_path)
                  if f.endswith(('.html', '.htm'))]
    for file in html_files:
        file_path = os.path.join(folder_path, file)
        result_file = process_html_table(file_path)
        print(f"Finish: {file_path}")
