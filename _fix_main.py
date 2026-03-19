from pathlib import Path
p = Path('app/main.py')
s = p.read_text(encoding='utf-8')
s = s.replace(\"{\\\\\\\", \\\\\\\".join(missing)}\", \"{', '.join(missing)}\")
p.write_text(s, encoding='utf-8')
