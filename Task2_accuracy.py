import json
import sys
import os
import re


# Normalize data cell content
def normalize_text(text):
    text = re.sub(r'\s+', '', text)
    symbol_replacements = {
        '>': '',
        '<': '',
        '-': '',
        '%': '',
        ',': '',
    }
    for output_pattern, standard_pattern in symbol_replacements.items():
        text = text.replace(output_pattern, standard_pattern)

    return text


# Extract data cell info
def extract_info(cell):
    # Extract data_cell and serial_number
    info = {
        'data_cell': cell.get('data_cell', ''),
        'serial_number': cell.get('serial_number', ''),
        'values': {}
    }

    for key, val in cell.items():
        if key.startswith('value') and val is not None:
            # Extract non-empty value
            if isinstance(val, dict):
                value_info = {}
                for attr in ['number', 'type', 'unit']:
                    value_info[attr] = val.get(attr, '')
                info['values'][key] = value_info

    return info


# Compare two cell info
def compare_cell(correct_cell, model_cell):
    correct_info = extract_info(correct_cell)
    model_info = extract_info(model_cell)

    # Compare serial_number
    if normalize_text(str(correct_info['serial_number'])) != normalize_text(str(model_info['serial_number'])):
        print(
            f"serial_number Different: Correct '{correct_info['serial_number']}' vs LLM '{model_info['serial_number']}'")
        return False

    # Compare data_cell
    if normalize_text(str(correct_info['data_cell'])) != normalize_text(str(model_info['data_cell'])):
        print(f"data_cell Different: Correct '{correct_info['data_cell']}' vs LLM '{model_info['data_cell']}'")
        return False

    # Compare values
    correct_vals = correct_info['values']
    model_vals = model_info['values']
    if set(correct_vals.keys()) != set(model_vals.keys()):
        only_correct = set(correct_vals.keys()) - set(model_vals.keys())
        only_model = set(model_vals.keys()) - set(correct_vals.keys())
        if only_correct:
            print(f"LLM failed to recognize value: {only_correct}")
        if only_model:
            print(f"LLM illusion: {only_model}")
        return False

    # Compare number, type, unit of each value
    all_match = True
    for vkey in sorted(correct_vals.keys()):
        c_val = correct_vals[vkey]
        m_val = model_vals[vkey]
        for attr in ['number', 'type', 'unit']:
            c_str = normalize_text(str(c_val.get(attr, '')))
            m_str = normalize_text(str(m_val.get(attr, '')))
            if c_str != m_str:
                print(f"{vkey} has Different '{attr}' : Correct'{c_val.get(attr)}' vs LLM '{m_val.get(attr)}'")
                all_match = False
    return all_match


# Count the total number of non-empty value
def count_values_in_file(data):
    total = 0
    for cell in data:
        for key, val in cell.items():
            if key.startswith('value') and val is not None:
                total += 1
    return total


# Compare gold standard and model output
def compare_file(correct_file, model_file):
    try:
        with open(correct_file, 'r', encoding='utf-8') as f:
            correct_data = json.load(f)
        with open(model_file, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
    except Exception as e:
        print(f"读取文件出错: {e}")
        return

    # Check if JSON contain data list
    if not isinstance(correct_data, list) or not isinstance(model_data, list):
        print("JSON Does not contain list")
        return

    # summary result
    total_correct_cells = len(correct_data)
    total_model_cells = len(model_data)
    total_correct_values = count_values_in_file(correct_data)
    total_model_values = count_values_in_file(model_data)

    # map data cell with serial_number
    model_cell_map = {}
    for cell in model_data:
        info = extract_info(cell)
        serial = info['serial_number']
        if serial:
            model_cell_map[serial] = cell

    recognized_cells = 0
    correct_cells = 0
    recognized_values = 0
    correct_values = 0

    print("Compare Result:")
    print("=" * 80)

    for correct_cell in correct_data:
        correct_info = extract_info(correct_cell)
        serial = correct_info['serial_number']

        if serial in model_cell_map:
            recognized_cells += 1
            model_cell = model_cell_map[serial]
            model_info = extract_info(model_cell)

            correct_value_keys = set(correct_info['values'].keys())
            model_value_keys = set(model_info['values'].keys())
            common_keys = correct_value_keys & model_value_keys
            recognized_values += len(common_keys)

            if compare_cell(correct_cell, model_cell):
                correct_cells += 1
                val_count = sum(1 for k, v in correct_cell.items() if k.startswith('value') and v is not None)
                correct_values += val_count
                print(f"Serial_number: {serial}: ✓ Correct")
            else:
                print(f"Serial_number: {serial}: ✗ Difference")
        else:
            print(f"Serial_number: {serial}: ✗ Not recognized")

    # Calculate results
    recognition_rate = recognized_cells / total_correct_cells if total_correct_cells > 0 else 0
    accuracy_rate = correct_cells / total_correct_cells if total_correct_cells > 0 else 0
    recall = correct_cells / total_model_cells if total_model_cells > 0 else 0

    print("\n" + "=" * 80)
    print("Results:")
    print(f"Total data_cell number: {total_correct_cells}")
    print(f"Recognized data_cell number: {recognized_cells}")
    print(f"LLM output data_cell number: {total_model_cells}")
    print(f"Correctly recognized data cell: {correct_cells}")
    print(f"Recognition rate: {recognition_rate * 100:.2f}%")
    print(f"Recall: {recall * 100:.2f}%")
    print(f"Accuracy rate: {accuracy_rate * 100:.2f}%")

    recognition_rate2 = recognized_values / total_correct_values if total_correct_values > 0 else 0
    accuracy_rate2 = correct_values / total_correct_values if total_correct_values > 0 else 0
    recall2 = correct_values / total_model_values if total_model_values > 0 else 0
    print("\n" + "=" * 80)
    print(f"Total non-empty value number: {total_correct_values}")
    print(f"Recognized value number: {recognized_values}")
    print(f"LLM output value number: {total_model_values}")
    print(f"Correctly recognized value: {correct_values}")
    print(f"Recognition rate: {recognition_rate2 * 100:.2f}%")
    print(f"Recall: {recall2 * 100:.2f}%")
    print(f"Accuracy rate: {accuracy_rate2 * 100:.2f}%")

    return True


# Compare files in gold standard folder and model output folder
def processfiles(json_folder, llm_folder):
    correct_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
    llm_files = [f for f in os.listdir(llm_folder) if f.endswith('.json')]

    correct_names = set(os.path.splitext(f)[0] for f in correct_files)

    for llm_file in llm_files:
        llm_name = os.path.splitext(llm_file)[0]
        if llm_name in correct_names:
            print(f"Compare file: {llm_name}")
            result = compare_file(os.path.join(json_folder, llm_file), os.path.join(llm_folder, llm_file))
            if result:
                print("\nSuccess！")
            else:
                print("\nFail！")


if __name__ == "__main__":

    correct_folder = ""  # Input gold standard folder
    llm_folder = ""  # Input model output folder

    result = processfiles(correct_folder, llm_folder)