import json

# Step 1: Read the file content
file_path = 'out.txt'

with open(file_path, 'r') as file:
    json_data = file.read()

# Step 2: Parse the JSON content
parsed_json = json.loads(json_data)

# Step 3: Write the parsed JSON data to a new file with pretty-printing
output_file_path = 'fulldv.txt'

with open(output_file_path, 'w') as output_file:
    json.dump(parsed_json, output_file, indent=4)
