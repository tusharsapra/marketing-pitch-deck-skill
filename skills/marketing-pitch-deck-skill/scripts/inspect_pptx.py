#!/usr/bin/env python3
"""Inspect native PPTX objects and text in presentation order; no rendering."""
import argparse
import json
from pathlib import Path
import posixpath
import sys
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
      'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'


def inspect(path, expected_slides=None):
    with ZipFile(path) as archive:
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        relationships = ET.fromstring(archive.read('ppt/_rels/presentation.xml.rels'))
        targets = {rel.get('Id'): rel.get('Target') for rel in relationships.findall(f'{{{REL}}}Relationship')
                   if rel.get('TargetMode') != 'External'}
        size = presentation.find('p:sldSz', NS)
        width, height = (int(size.get(key)) for key in ('cx', 'cy')) if size is not None else (0, 0)
        slides, warnings = [], []
        for ordinal, entry in enumerate(presentation.findall('p:sldIdLst/p:sldId', NS), 1):
            rid = entry.get(f"{{{NS['r']}}}id")
            target = targets.get(rid)
            if not target:
                raise ValueError(f'Missing slide relationship {rid}')
            part = posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('ppt', target))
            if not part.startswith('ppt/'):
                raise ValueError(f'Unexpected slide path: {part}')
            root = ET.fromstring(archive.read(part))
            text = [node.text or '' for node in root.findall('.//a:t', NS)]
            groups = len(root.findall('.//p:grpSp', NS))
            bounds = []
            tree = root.find('p:cSld/p:spTree', NS)
            if tree is not None and width and height:
                for shape in tree:
                    transform = shape.find('p:spPr/a:xfrm', NS)
                    if transform is None:
                        transform = shape.find('p:xfrm', NS)
                    if transform is None or transform.get('rot'):
                        continue
                    off, ext = transform.find('a:off', NS), transform.find('a:ext', NS)
                    if off is None or ext is None:
                        continue
                    x, y, cx, cy = [int(node.get(key)) for node, key in
                                    ((off, 'x'), (off, 'y'), (ext, 'cx'), (ext, 'cy'))]
                    if x < 0 or y < 0 or x + cx > width + 10 or y + cy > height + 10:
                        bounds.append({'x': x, 'y': y, 'cx': cx, 'cy': cy})
            info = {'slide': ordinal, 'part': part, 'text': text,
                    'text_shapes': len(root.findall('.//p:sp/p:txBody', NS)),
                    'tables': len(root.findall('.//a:tbl', NS)),
                    'charts': len(root.findall('.//c:chart', NS)),
                    'images': len(root.findall('.//p:pic', NS)),
                    'groups': groups, 'out_of_canvas_objects': bounds}
            slides.append(info)
            if bounds:
                warnings.append(f'Slide {ordinal}: {len(bounds)} unrotated top-level object(s) extend beyond canvas')
            if groups:
                warnings.append(f'Slide {ordinal}: group transforms are not checked for bounds')
        if not slides:
            raise ValueError('No slides found in presentation order')
        if expected_slides is not None and len(slides) != expected_slides:
            raise ValueError(f'Found {len(slides)} slides; expected {expected_slides}')
        return {'slide_count': len(slides), 'canvas_emu': [width, height], 'slides': slides,
                'warnings': warnings,
                'limitations': 'Structural inspection only. Does not verify rendering, source truth, font availability, object usability or visual quality.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('presentation', type=Path)
    parser.add_argument('--expected-slides', type=int)
    parser.add_argument('--json', type=Path, dest='json_output')
    args = parser.parse_args()
    try:
        result = inspect(args.presentation, args.expected_slides)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError, TypeError, KeyError, BadZipFile, ET.ParseError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f"Slides: {result['slide_count']}")
    for slide in result['slides']:
        print(f"{slide['slide']:02}: text shapes={slide['text_shapes']}, tables={slide['tables']}, charts={slide['charts']}, images={slide['images']}")
    for warning in result['warnings']:
        print(f'WARNING: {warning}')
    print(result['limitations'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
