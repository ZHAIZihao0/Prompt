import json
import re
import unicodedata

def normalize_text(text):

    if text is None:
        return None

    text = unicodedata.normalize('NFKC', text.strip()) #Change Fullwidth to halfwidth
    char_replacements = {
        '\u2212': '-',  # −
        '\u2010': '-',  # ‐
        '\u2011': '-',  # ‑
        '\u2012': '-',  # ‒
        '\u2013': '-',  # –
        '\u2014': '-',  # —
        '\u002D': '-',  # -
        '\u2213': '±',  # ∓
        '\u00B1': '±',  # ±
        '\u2044': '/',  # ⁄
        '\u2215': '/',  # ∕
        '\u002F': '/',  # /
        '\u2264': '≤',  # ≤
        '\u2265': '≥',  # ≥
        '\u003C': '<',  # <
        '\u003E': '>',  # >
        '\uFF0D': '-',  # －
    }
    pattern_replacements = {
        '>=': '≥',
        '<=': '≤',
        '!=': '≠',
    }

    for unicode_char, standard_char in char_replacements.items():
      text = text.replace(unicode_char, standard_char)
    for output_pattern, standard_pattern in pattern_replacements.items():
      text = text.replace(output_pattern, standard_pattern)

    operators = ['=', '-', '+', '/', '*', '<', '>', '(', ')', ',']
    for op in operators:
      text = re.sub(r'\s*' + re.escape(op) + r'\s*', op, text)
    #text = re.sub(r'\s+', ' ', text)
    return text

def extract_all_cell_info(cell_data):
    """Extract data cell info"""
    info = {}

    # Extract data cell value
    if 'data cell' in cell_data:
      info['data_cell_value'] = normalize_text(cell_data['data cell'])
    else:
      info['data_cell_value'] = None


    # Extract row headers
    info['row_headers'] = {}
    if 'row header' in cell_data:
      row_header_data = cell_data['row header']

      row_values = {}
      for level in ['row header level-1', 'row header level-2', 'row header level-3']:
        if level in row_header_data:
          normalized = normalize_text(row_header_data[level])
          row_values[level] = normalized if normalized else None  # Transfer "" to None
        else:
          row_values[level] = None

      if row_values['row header level-3'] is not None:
        if row_values['row header level-3'] == row_values['row header level-2']:
          row_values['row header level-3'] = None
        elif row_values['row header level-3'] == row_values['row header level-1']:
          row_values['row header level-3'] = None

      if row_values['row header level-2'] is not None:
        if row_values['row header level-2'] == row_values['row header level-1']:
          row_values['row header level-2'] = None

      for level in ['row header level-1', 'row header level-2', 'row header level-3']:
        info['row_headers'][level] = row_values[level]

    else:
      for level in ['row header level-1', 'row header level-2', 'row header level-3']:
        info['row_headers'][level] = None

    # Extract column headers
    info['column_headers'] = {}
    if 'column header' in cell_data:
      column_header_data = cell_data['column header']

      column_values = {}
      for level in ['column header level-1', 'column header level-2', 'column header level-3']:
        if level in column_header_data:
          normalized = normalize_text(column_header_data[level])
          column_values[level] = normalized if normalized else None # Transfer "" to None
        else:
          column_values[level] = None

      if column_values['column header level-3'] is not None:
        if column_values['column header level-3'] == column_values['column header level-2']:
          column_values['column header level-3'] = None
        elif column_values['column header level-3'] == column_values['column header level-1']:
          column_values['column header level-3'] = None

      if column_values['column header level-2'] is not None:
        if column_values['column header level-2'] == column_values['column header level-1']:
          column_values['column header level-2'] = None

      for level in ['column header level-1', 'column header level-2', 'column header level-3']:
        info['column_headers'][level] = column_values[level]

    else:
      for level in ['column header level-1', 'column header level-2', 'column header level-3']:
        info['column_headers'][level] = None

    # Extract serial_number
    if 'serial_number' in cell_data :
        info['serial_number'] = normalize_text(cell_data['serial_number'])
    else:
        info['serial_number'] = None

    return info

def compare_cell(correct_cell, model_cell):
    """Compare data cells info"""
    correct_info = extract_all_cell_info(correct_cell)
    model_info = extract_all_cell_info(model_cell)

    # Compare data cell value
    if correct_info['data_cell_value'] != model_info['data_cell_value']:
        return False


    # Compare all level row headers
    for level in ['row header level-1', 'row header level-2', 'row header level-3']:
        if correct_info['row_headers'].get(level) != model_info['row_headers'].get(level):
            return False

    # Compare all level column headers
    for level in ['column header level-1', 'column header level-2', 'column header level-3']:
        if correct_info['column_headers'].get(level) != model_info['column_headers'].get(level):
            return False

    # Compare serial_number
    if correct_info['serial_number'] != model_info['serial_number']:
        return False

    return True

def compare_single_file(correct_file, model_file):
    """Compare correct JSON file and model output"""
    try:
        # Read coorect file
        with open(correct_file, 'r', encoding='utf-8') as f:
            correct_data = json.load(f)

        # Read model output
        with open(model_file, 'r', encoding='utf-8') as f:
            model_data = json.load(f)

        # Creat map for model data cells
        model_cell_map = {}
        for cell in model_data:
            info = extract_all_cell_info(cell)
            serial_number = info['serial_number']
            if serial_number:  # Only process data cells without serial_number
              model_cell_map[serial_number] = cell

        total_cells = len(correct_data)
        model_cells = len(model_data)
        recognized_cells = 0
        correct_cells = 0

        print("Compare Result:")
        print("=" * 80)

        for correct_cell in correct_data:
          correct_info = extract_all_cell_info(correct_cell)
          serial_number = correct_info['serial_number']


          if serial_number in model_cell_map:
            recognized_cells += 1
            model_cell = model_cell_map[serial_number]

            if compare_cell(correct_cell, model_cell):
               correct_cells += 1
               print(f"{serial_number} (ID: {serial_number}): ✓ Correct")
            else:
               print(f"{serial_number} (ID: {serial_number}): ✗ Difference")
               # Show the difference
               model_info = extract_all_cell_info(model_cell)

               if correct_info['data_cell_value'] != model_info['data_cell_value']:
                 print(f"  Data cell value: '{correct_info['data_cell_value']}' vs '{model_info['data_cell_value']}'")

               for level in ['row header level-1', 'row header level-2', 'row header level-3']:
                  if correct_info['row_headers'].get(level) != model_info['row_headers'].get(level):
                      print(f"  {level}: '{correct_info['row_headers'].get(level)}' vs '{model_info['row_headers'].get(level)}'")

               for level in ['column header level-1', 'column header level-2', 'column header level-3']:
                  if correct_info['column_headers'].get(level) != model_info['column_headers'].get(level):
                      print(f"  {level}: '{correct_info['column_headers'].get(level)}' vs '{model_info['column_headers'].get(level)}'")
          else:
            print(f"{serial_number} (serial_number: {serial_number}): ✗ Not recognized")

        # Calculation
        recognition_rate = recognized_cells / total_cells if total_cells > 0 else 0
        accuracy_rate = correct_cells / total_cells if total_cells > 0 else 0
        recall = correct_cells / model_cells if model_cells > 0 else 0

        print("=" * 80)
        print("Results:")
        print(f"Total data cell numbers: {total_cells}")
        print(f"Recognized data cell numbers: {recognized_cells}")
        print(f"LLM output data cell numbers: {model_cells}")
        print(f"Correctly recognized data cell numbers: {correct_cells}")
        print(f"Recognition rate: {recognition_rate:.4f} ({recognition_rate*100:.2f}%)")
        print(f"Recall: {recall:.4f} ({recall*100:.2f}%)")
        print(f"Accuracy: {accuracy_rate:.4f} ({accuracy_rate*100:.2f}%)")

        return {
            'total_cells': total_cells,
            'recognized_cells': recognized_cells,
            'correct_cells': correct_cells,
            'recognition_rate': recognition_rate,
            'recall': recall,
            'accuracy_rate': accuracy_rate
        }

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: JSON error - {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    correct_file = ""           # correct file
    model_file = ""         # model file
    
    print(f"Compare files:")
    print(f"Correct file: {correct_file}")
    print(f"Model file: {model_file}")
    print()
    
    result = compare_single_file(correct_file, model_file)
    
    if result:
        print("\nSuccess！")
    else:
        print("\nFail！")
