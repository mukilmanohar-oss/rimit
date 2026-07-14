
import re

with open("E:/SPEC/src/components/views/students.tsx", "r", encoding="utf-8", errors="replace") as f:
    content = f.read()

# Add aggregator import
content = content.replace(
    "import { admissions, type Student, type UserProfile } from '@/lib/api';",
    "import { admissions, aggregator, type Student, type UserProfile } from '@/lib/api';"
)

with open("C:/Users/hp/.gemini/antigravity/brain/1755859a-999a-4356-915b-86f9e15640ba/scratch/patch_students.py", "r", encoding="utf-8") as f:
    patch_code = f.read()

# Extract new_form from the python file string
new_form = patch_code.split("new_form = \"\"\"")[1].split("\"\"\"")[0]

start_token = "function StudentRegistrationForm"
end_token = "return (\n      <div>"

import re
pattern = re.compile(r"function StudentRegistrationForm.*?return \(\s*<div>.*?</div>\s*\);\s*}", re.DOTALL)
content = pattern.sub(lambda m: new_form, content, count=1)

with open("E:/SPEC/src/components/views/students.tsx", "w", encoding="utf-8") as f:
    f.write(content)

