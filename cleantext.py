

import json
import re

def clean_text(text):

    if text is None:
        return None


    original_text = text

    try:

        unicode_escapes = {
            '\\u2009': ' ',
            '\\u200a': ' ',
            '\\u200b': ' ',
            '\\u200c': ' ',
            '\\u200d': ' ',
            '\\u202f': ' ',
            '\\u00a0': ' ',  
        }

        cleaned = text
        for escape_seq, replacement in unicode_escapes.items():
            cleaned = cleaned.replace(escape_seq, replacement)


        cleaned = re.sub(r'\\\(', '(', cleaned)
        cleaned = re.sub(r'\\\)', ')', cleaned)
        cleaned = re.sub(r'\\%', '%', cleaned)


        cleaned = re.sub(r'_', '', cleaned)


        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    except Exception as e:
        print(f"error: {e}, info: {original_text}")
        return original_text

def clean_model_output_file(input_file, output_file):

    try:

        with open(input_file, 'r', encoding='utf-8') as f:
            model_data = json.load(f)


        cleaned_data = []
        changes_count = 0

        for cell in model_data:
            cleaned_cell = cell.copy()
            cell_changed = False


            if 'row header' in cleaned_cell:
                for level in ['row header level-1', 'row header level-2', 'row header level-3']:
                    if level in cleaned_cell['row header'] and 'value' in cleaned_cell['row header'][level]:
                        original = cleaned_cell['row header'][level]['value']
                        cleaned = clean_text(original)
                        if original != cleaned:
                            cleaned_cell['row header'][level]['value'] = cleaned
                            cell_changed = True
                            changes_count += 1


            if 'column header' in cleaned_cell:
                for level in ['column header level-1', 'column header level-2', 'column header level-3']:
                    if level in cleaned_cell['column header'] and 'value' in cleaned_cell['column header'][level]:
                        original = cleaned_cell['column header'][level]['value']
                        cleaned = clean_text(original)
                        if original != cleaned:
                            cleaned_cell['column header'][level]['value'] = cleaned
                            cell_changed = True
                            changes_count += 1


            if 'data cell' in cleaned_cell and 'value' in cleaned_cell['data cell']:
                original = cleaned_cell['data cell']['value']
                cleaned = clean_text(original)
                if original != cleaned:
                    cleaned_cell['data cell']['value'] = cleaned
                    cell_changed = True
                    changes_count += 1

            cleaned_data.append(cleaned_cell)


        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

        print(f"Finished！")
        print(f"Input file: {input_file}")
        print(f"Output file: {output_file}")
        print(f"Processsed data cell: {len(cleaned_data)}")
        print(f"Changed data cell: {changes_count}")


        return True

    except FileNotFoundError:
        print(f"Error: file not found - {input_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: JSONDecodeError - {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

input_file = "/content/1204_table1.json"
output_file = "/content/1204_table1_clean.json"

print("Start...")
print("=" * 50)

success = clean_model_output_file(input_file, output_file)

if success:
    print("=" * 50)
    print("Success！")
    print(f"Data saved as: {output_file}")

else:
    print("Failed！")