import os
import re

def fix_nulls(text):
    # Matches: deal == null, deal.get("id") == null, etc.
    text = re.sub(r'([a-zA-Z0-9_]+(?:\.get\("[a-zA-Z0-9_ ]+"\))?)\s*==\s*null', r'isNull(\1)', text)
    text = re.sub(r'([a-zA-Z0-9_]+(?:\.get\("[a-zA-Z0-9_ ]+"\))?)\s*!=\s*null', r'!isNull(\1)', text)
    return text

def fix_type_errors(text):
    # If the user is facing "In Criteria left expression is of type TEXT and right expression is of type NUMBER and the operator == is not valid",
    # This usually means something like `if(stage == 0)` where stage is text.
    # But usually it's `zoho.crm.searchRecords(..., "(What_Id:equals:" + dealId + ")")`
    return text

directory = r'c:\Development\Projects\zoho-functions\v3\activity'
for f in os.listdir(directory):
    if f.endswith('.deluge'):
        path = os.path.join(directory, f)
        with open(path, 'r', encoding='utf-8') as file:
            c = file.read()
        
        new_c = fix_nulls(c)
        if c != new_c:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(new_c)
            print(f'Fixed nulls in {f}')
