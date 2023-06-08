import json 
import os 
json_file = r'.\a.json' 
bat_file = r'.\json_to_environment_run_after_the_py.bat' 
with open(json_file) as file: 
    data = json.load(file) 
with open(bat_file, 'w') as file: 
    file.write(f'@echo off\n') 
    for key, value in data.items(): 
        if isinstance(value, list): 
            value_string = '[' + (', '.join('"' + str(item) + '"' if isinstance(item, str) else str(item) for item in value)) + ']' 
        else: 
            value_string = '"' + str(value) + '"' if isinstance(value, str) else str(value) 
        file.write(f'set "{key}={value_string}"\n') 
    file.write(f'goto :eof\n') 
#print(f'{bat_file} generated.') 
#print(f'{bat_file} generated.') 
