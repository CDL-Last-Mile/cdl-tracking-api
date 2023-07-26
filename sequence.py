import requests
import os
from datetime import datetime

try:
    response = requests.get('http://localhost/orderfinder/subscription/update')
    response.raise_for_status()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "lastreport.txt")
    append_write = 'w' 
    if os.path.exists(file_path):
        append_write = 'a'
        
    with open(file_path, append_write) as f:
        f.write(str(datetime.now()))
        f.write('\n')
    
except requests.exceptions.HTTPError as error:
    print(error)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "lasterror.txt")
    append_write = 'w' 
    if os.path.exists(file_path):
        append_write = 'a' 
        
    with open(file_path, append_write) as f:
        f.write(str(datetime.now()))
        f.write(str(error))
        f.write('\n')
 