"""Curated issue records embedded in two repository documents, never live state."""
import json
from pathlib import Path
from local_evidence import read_bytes

ROOT = Path(__file__).resolve().parent
DOCUMENTS = ('docs/LEARNING-AND-ISSUES.md', 'docs/NATIVE-VERIFICATION-GAP.md')
START, END = '<!-- admin-issues:start -->', '<!-- admin-issues:end -->'
FIELDS = {'id', 'title', 'scope', 'status', 'detail', 'suggestedFix'}


def read(root=ROOT):
    result = []
    for name in DOCUMENTS:
        try:
            raw = read_bytes(root / name, 256 * 1024)
            if len(raw) > 256 * 1024:
                raise ValueError('oversized document')
            text = raw.decode('utf-8')
            if text.count(START) != 1 or text.count(END) != 1:
                raise ValueError('missing or ambiguous inventory')
            body = text.split(START, 1)[1].split(END, 1)[0].strip()
            if not body.startswith('```json\n') or not body.endswith('\n```'):
                raise ValueError('invalid inventory fence')
            def unique(pairs):
                values = {}
                for key, value in pairs:
                    if key in values:
                        raise ValueError('duplicate field')
                    values[key] = value
                return values
            rows = json.loads(body[8:-4], object_pairs_hook=unique)
            if not isinstance(rows, list) or len(rows) > 16:
                raise ValueError('invalid inventory')
            seen = set()
            for row in rows:
                if not isinstance(row, dict) or set(row) != FIELDS or any(
                        not isinstance(value, str) or not value.strip() or len(value) > 1024 for value in row.values()):
                    raise ValueError('invalid issue')
                if row['id'] in seen or row['status'] not in ('Documented gap', 'Verification pending'):
                    raise ValueError('invalid identity or status')
                seen.add(row['id'])
            result.extend({**row, 'id':name + ':' + row['id'], 'source':'Repository planning inventory · ' + name,
                           'updatedAt':None, 'timeLabel':'Live observation', 'documentIssue':True} for row in rows)
        except (OSError, ValueError, RecursionError):
            result.append(dict(title='Project issue inventory unavailable', scope='Network', status='Unknown',
                               detail='Document inventory could not be read completely. No healthy or resolved state is inferred.',
                               source='Repository planning inventory · ' + name, updatedAt=None,
                               documentIssue=True, suggestedFix='Review the curated issue block in the named repository document.'))
    return result
