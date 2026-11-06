"""Build the merged Azure CLI extension index.

Takes Microsoft's official index and replaces only the 'azure-devops' entry with the
ROSEN fork wheel(s), so every other extension keeps installing/updating as usual.

usage: build_index.py <out.json> <wheel-url> <wheel-file> [<wheel-url> <wheel-file> ...]
"""
import copy
import hashlib
import json
import re
import sys
import urllib.request

OFFICIAL_INDEX = 'https://aka.ms/azure-cli-extension-index-v1'


def main(argv):
    out, pairs = argv[0], argv[1:]
    if not pairs or len(pairs) % 2:
        raise SystemExit(__doc__)

    with urllib.request.urlopen(OFFICIAL_INDEX) as response:
        index = json.load(response)

    # Reuse upstream's metadata shape; current wheels carry no metadata.json.
    template = index['extensions']['azure-devops'][-1]['metadata']
    entries = []
    for url, wheel in zip(pairs[0::2], pairs[1::2]):
        filename = wheel.replace('\\', '/').rsplit('/', 1)[-1]
        version = re.match(r'azure_devops-(.+?)-py2', filename).group(1)
        with open(wheel, 'rb') as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        metadata = copy.deepcopy(template)
        metadata['version'] = version
        entries.append({'downloadUrl': url, 'filename': filename, 'metadata': metadata, 'sha256Digest': digest})

    index['extensions']['azure-devops'] = entries
    with open(out, 'w') as f:
        json.dump(index, f)
    print('{} extensions; azure-devops -> {}'.format(
        len(index['extensions']), [e['metadata']['version'] for e in entries]))


if __name__ == '__main__':
    main(sys.argv[1:])
