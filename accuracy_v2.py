
import json
import re

def normalize_text(text):

    if text is None:
        return None

    return re.sub(r'\s+', '', text.strip())

def extract_all_cell_info(cell_data):

    info = {}

    # Extract data cell value
    if 'data cell' in cell_data and 'value' in cell_data['data cell']:
        info['data_cell_value'] = normalize_text(cell_data['data cell']['value'])
    else:
        info['data_cell_value'] = None

    # Extract location
    if 'location' in cell_data and 'value' in cell_data['location']:
        info['location_value'] = normalize_text(cell_data['location']['value'])
    else:
        info['location_value'] = None

    # Extract row headers
    info['row_headers'] = {}
    if 'row header' in cell_data:
        row_header_data = cell_data['row header']
        for level in ['row header level-1', 'row header level-2', 'row header level-3']:
            if level in row_header_data and 'value' in row_header_data[level]:
                info['row_headers'][level] = normalize_text(row_header_data[level]['value'])
            else:
                info['row_headers'][level] = None

    # Extract column headers
    info['column_headers'] = {}
    if 'column header' in cell_data:
        column_header_data = cell_data['column header']
        for level in ['column header level-1', 'column header level-2', 'column header level-3']:
            if level in column_header_data and 'value' in column_header_data[level]:
                info['column_headers'][level] = normalize_text(column_header_data[level]['value'])
            else:
                info['column_headers'][level] = None

    return info

def compare_cell_completely(correct_cell, model_cell):

    correct_info = extract_all_cell_info(correct_cell)
    model_info = extract_all_cell_info(model_cell)

    # Compare data cell value
    if correct_info['data_cell_value'] != model_info['data_cell_value']:
        return False

    # Compare location
    if correct_info['location_value'] != model_info['location_value']:
        return False

    # Compare row headers
    for level in ['row header level-1', 'row header level-2', 'row header level-3']:
        if correct_info['row_headers'].get(level) != model_info['row_headers'].get(level):
            return False

    # Compare column headers
    for level in ['column header level-1', 'column header level-2', 'column header level-3']:
        if correct_info['column_headers'].get(level) != model_info['column_headers'].get(level):
            return False

    return True

def compare_single_file(correct_file, model_file):

    try:
        # load correct file
        with open(correct_file, 'r', encoding='utf-8') as f:
            correct_data = json.load(f)

        # load model output
        with open(model_file, 'r', encoding='utf-8') as f:
            model_data = json.load(f)

        # creat location map
        model_cell_map = {}
        for cell in model_data:
            location = normalize_text(cell['location']['value'])
            model_cell_map[location] = cell

        total_cells = len(correct_data)
        recognized_cells = 0
        correct_cells = 0

        print("Result:")
        print("=" * 80)

        for correct_cell in correct_data:
            location = normalize_text(correct_cell['location']['value'])

            if location in model_cell_map:
                recognized_cells += 1
                model_cell = model_cell_map[location]

                if compare_cell_completely(correct_cell, model_cell):
                    correct_cells += 1
                    print(f"{location}: ✓ Correct")
                else:
                    print(f"{location}: ✗ Wrong")

                    correct_info = extract_all_cell_info(correct_cell)
                    model_info = extract_all_cell_info(model_cell)

                    if correct_info['data_cell_value'] != model_info['data_cell_value']:
                        print(f"  Value: '{correct_info['data_cell_value']}' vs '{model_info['data_cell_value']}'")

                    for level in ['row header level-1', 'row header level-2', 'row header level-3']:
                        if correct_info['row_headers'].get(level) != model_info['row_headers'].get(level):
                            print(f"  {level}: '{correct_info['row_headers'].get(level)}' vs '{model_info['row_headers'].get(level)}'")

                    for level in ['column header level-1', 'column header level-2', 'column header level-3']:
                        if correct_info['column_headers'].get(level) != model_info['column_headers'].get(level):
                            print(f"  {level}: '{correct_info['column_headers'].get(level)}' vs '{model_info['column_headers'].get(level)}'")
            else:
                print(f"{location}: ✗ Data cell not recognized")

        # Calculate accuracy
        recognition_rate = recognized_cells / total_cells if total_cells > 0 else 0
        accuracy_rate = correct_cells / total_cells if total_cells > 0 else 0

        print("=" * 80)
        print("Final Result:")
        print(f"Total data cell number: {total_cells}")
        print(f"Recognized data cell number: {recognized_cells}")
        print(f"Correct data cell number: {correct_cells}")
        print(f"Recognition rate: {recognition_rate:.4f} ({recognition_rate*100:.2f}%)")
        print(f"Accuracy: {accuracy_rate:.4f} ({accuracy_rate*100:.2f}%)")

        return {
            'total_cells': total_cells,
            'recognized_cells': recognized_cells,
            'correct_cells': correct_cells,
            'recognition_rate': recognition_rate,
            'accuracy_rate': accuracy_rate
        }

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: JSONDecodeError - {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

correct_file =           # Correct file
model_file =          # Model output

print(f"Start processing:")
print(f"Coorect file: {correct_file}")
print(f"Model file: {model_file}")
print()

result = compare_single_file(correct_file, model_file)

if result:
    print("\nSuccess！")
else:
    print("\nFailed！")
