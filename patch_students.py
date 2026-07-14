
import re

with open("E:/SPEC/src/components/views/students.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Add aggregator import
if "import { aggregator" not in content:
    content = content.replace(
        "import { admissions, type Student, type UserProfile } from '@/lib/api';",
        "import { admissions, aggregator, type Student, type UserProfile } from '@/lib/api';"
    )

with open("E:/SPEC/src/components/views/students.tsx", "w", encoding="utf-8") as f:
    f.write(content)

