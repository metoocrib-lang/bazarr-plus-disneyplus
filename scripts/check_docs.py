"""Check repository documentation links and provider mapping examples offline."""
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location('documented_provider', ROOT / 'provider/provider.py')
    provider = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider)
    documents = [ROOT / 'README.md', *sorted((ROOT / 'docs').glob('*.md'))]
    errors, examples = [], 0
    for document in documents:
        text = document.read_text(encoding='utf-8')
        prose = re.sub(r'```.*?```', '', text, flags=re.S)
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', prose):
            target = target.strip('<>')
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            if not (document.parent / unquote(url.path)).exists():
                errors.append(f'{document.relative_to(ROOT)}: missing target {target}')
        for block in re.findall(r'```json\s*\n(.*?)\n```', text, re.S):
            try:
                data = json.loads(block)
                if isinstance(data, list) and data and all(
                        isinstance(item, dict) and 'mapping' in item for item in data):
                    for item in data:
                        provider.parse_mapping(item['mapping'])
                        if not provider._valid_disney_url(item['series_url']):
                            raise ValueError('Invalid catalog URL in mapping example')
                    examples += 1
            except (ValueError, KeyError, TypeError) as error:
                errors.append(f'{document.relative_to(ROOT)}: {error}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'{len(documents)} Markdown files checked; {examples} mapping examples valid.')


if __name__ == '__main__':
    main()
