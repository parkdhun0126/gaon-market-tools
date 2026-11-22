"""Simple publication-only repository scan; not a substitute for professional audit."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
    'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'openai_key':r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b',
    'github_token':r'\bgh[pousr]_[A-Za-z0-9]{20,}\b',
    'aws_key':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'secret_assignment':r'(?im)^\s*(?:api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*[\"\']?[^\s#\"\']{8,}',
}

def main()->int:
    checked=0; issues=[]
    for path in ROOT.rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc': continue
        if '.git' in path.parts or '.venv' in path.parts or 'venv' in path.parts:
            continue  # CI checkout has legitimate Git metadata; scan published text only.
        checked+=1
        content=path.read_text(encoding='utf-8')
        for title,regex in PATTERNS.items():
            if re.search(regex,content):
                issues.append(f'{path.relative_to(ROOT)}: {title}')
    print(f'{checked} files scanned; {len(issues)} findings')
    for item in issues: print(item)
    return 1 if issues else 0

if __name__=='__main__':raise SystemExit(main())
