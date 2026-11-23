#!/usr/bin/env python3
"""Render an approved pitched major-key MSCZ; no browser or publishing actions."""
import argparse
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

KEYS = {'Cb': -7, 'Gb': -6, 'Db': -5, 'Ab': -4, 'Eb': -3,
        'Bb': -2, 'F': -1, 'C': 0, 'G': 1, 'D': 2, 'A': 3,
        'E': 4, 'B': 5, 'F#': 6, 'C#': 7}


def read_score(path):
    with ZipFile(path) as z:
        if z.testzip() is not None:
            raise ValueError(f'Invalid MSCZ archive: {path}')
        names = [n for n in z.namelist() if n.endswith('.mscx')]
        if len(names) != 1:
            raise ValueError('Expected exactly one master MSCX inside MSCZ')
        return ET.fromstring(z.read(names[0]))


def spanners(element):
    result = []
    for node in element.findall('.//Spanner'):
        node = copy.deepcopy(node)
        for parent in node.iter():
            for child in list(parent):
                if child.tag == 'eid':
                    parent.remove(child)
        result.append(ET.tostring(node, encoding='unicode'))
    return tuple(result)


def rhythm_layout(root):
    result = []
    for staff in root.findall('./Score/Staff'):
        measures = []
        for m in staff.findall('Measure'):
            events = []
            for voice in m.findall('voice'):
                for e in voice:
                    if e.tag in ('Chord', 'Rest'):
                        events.append((e.tag, e.findtext('durationType'), e.findtext('duration'),
                                       e.findtext('dots'),
                                       tuple(''.join(x.itertext()) for x in e.findall('Lyrics')),
                                       spanners(e)))
            bars = tuple((b.findtext('subtype'), b.findtext('visible'))
                         for b in m.findall('.//BarLine'))
            measures.append((m.get('len'), m.findtext('irregular'), m.findtext('noOffset'),
                             m.findtext('measureNumberMode'),
                             tuple(x.findtext('subtype') for x in m.findall('LayoutBreak')),
                             bars, events))
        result.append(measures)
    return result


def pitches(root):
    return [int(n.findtext('pitch')) for n in root.findall('.//Chord/Note')]


def run(mscore, *args):
    result = subprocess.run([str(mscore), *map(str, args)], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'MuseScore failed ({result.returncode}): {result.stderr[-1500:]}')


def verify(before, after, fifths, allowed_shifts):
    key = after.findtext('.//KeySig/concertKey')
    if key != str(fifths):
        raise ValueError(f'Wrong exported key: {key}, expected {fifths}')
    pa, pb = pitches(before), pitches(after)
    if not pa or len(pa) != len(pb):
        raise ValueError('Missing or changed note count')
    shifts = {b-a for a, b in zip(pa, pb)}
    if len(shifts) != 1 or next(iter(shifts)) not in allowed_shifts:
        raise ValueError(f'Unexpected pitch shifts: {shifts}, allowed {allowed_shifts}')
    shift = next(iter(shifts))
    if rhythm_layout(before) != rhythm_layout(after):
        raise ValueError('Rhythm, lyrics, spanners, partial measures, or layout changed')
    ha, hb = before.findall('.//Harmony/harmonyInfo'), after.findall('.//Harmony/harmonyInfo')
    if len(ha) != len(hb):
        raise ValueError('Chord count changed')
    for a, b in zip(ha, hb):
        if a.findtext('name') != b.findtext('name'):
            raise ValueError('Chord quality changed')
        for tag in ('root', 'bass'):
            av, bv = a.findtext(tag), b.findtext(tag)
            if av is None:
                if bv is not None:
                    raise ValueError(f'Unexpected chord {tag}')
            elif bv is None or (7*(int(bv)-int(av))) % 12 != shift % 12:
                raise ValueError(f'Incorrect chord {tag} transposition')
    return {'semitones': shift, 'notes': len(pa), 'chords': len(ha)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--out-dir', type=Path, required=True)
    p.add_argument('--name', help='Song filename, without key or extension')
    p.add_argument('--keys', nargs='+', choices=list(KEYS))
    p.add_argument('--shifts', nargs='+', default=[], metavar='KEY=SEMITONES')
    p.add_argument('--mscore', type=Path, default=Path('/Applications/MuseScore 4.app/Contents/MacOS/mscore'))
    p.add_argument('--work-dir', type=Path, default=Path.cwd()/'work'/'musescore-render')
    p.add_argument('--dpi', type=int, default=240)
    p.add_argument('--zip', action='store_true')
    args = p.parse_args()
    if not args.source.is_file() or args.source.suffix.lower() != '.mscz':
        p.error('Source must be an existing approved native .mscz file')
    if not args.mscore.is_file():
        p.error('MuseScore executable not found; use --mscore')
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        p.error('Use a new or empty output directory; existing files are never overwritten')
    if not 72 <= args.dpi <= 600:
        p.error('Image DPI must be between 72 and 600')
    before = read_score(args.source)
    first = before.find('.//KeySig')
    if first is None or first.findtext('mode', 'major') not in ('major', 'none', 'unknown'):
        p.error('This helper expects a pitched major-key score; handle other modes separately')
    source_fifths = int(first.findtext('concertKey'))
    source_pc = (7*source_fifths) % 12
    labels = args.keys or [next(k for k, v in KEYS.items() if v == source_fifths)]
    if len(set(labels)) != len(labels):
        p.error('Duplicate target keys')
    explicit = {}
    for text in args.shifts:
        key, value = text.split('=', 1)
        if key not in labels:
            p.error(f'Shift provided for unrequested key: {key}')
        explicit[key] = int(value)
        if not -11 <= explicit[key] <= 11:
            p.error('Explicit shifts must be within one octave')
        if (source_pc+explicit[key]) % 12 != (7*KEYS[key]) % 12:
            p.error(f'Shift does not produce requested key: {key}')
    name = unicodedata.normalize('NFC', args.name or args.source.stem)
    if name in ('', '.', '..') or '/' in name or '\\' in name:
        p.error('Name must be a filename, not a path')
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='variants-', dir=args.work_dir))
    created, reports = [], []
    for key in labels:
        fifths = KEYS[key]
        raw = ((7*fifths) % 12-source_pc) % 12
        shift = explicit.get(key)
        allowed = {shift} if shift is not None else ({0} if raw == 0 else {raw, raw-12} if raw == 6 else {raw if raw < 6 else raw-12})
        stage = work/key.replace('#', 'sharp')
        stage.mkdir()
        score = stage/'score.mscz'
        if fifths == source_fifths and (shift is None or shift == 0):
            shutil.copyfile(args.source, score)
        else:
            options = dict(mode='by_key', direction='closest' if shift is None else 'up' if shift > 0 else 'down',
                           targetKey=fifths, transposeKeySignatures=True,
                           transposeChordNames=True, useDoubleSharpsFlats=False)
            run(args.mscore, args.source, '--transpose', json.dumps(options), '-o', score)
        report = verify(before, read_score(score), fifths, allowed)
        run(args.mscore, score, '-o', stage/'score.pdf')
        run(args.mscore, score, '-r', args.dpi, '-o', stage/'page.png')
        pages = sorted(stage.glob('page-*.png'), key=lambda x:int(re.search(r'-(\d+)\.png$', x.name).group(1)))
        if not pages and (stage/'page.png').exists():
            pages = [stage/'page.png']
        if not pages or not (stage/'score.pdf').is_file():
            raise ValueError(f'Export missing for {key}')
        stem = f'{name}_{key}'
        files = [(score, args.out_dir/f'{stem}.mscz'), (stage/'score.pdf', args.out_dir/f'{stem}.pdf')]
        files += [(pg, args.out_dir/(f'{stem}.png' if len(pages) == 1 else f'{stem}_p{i:02}.png'))
                  for i, pg in enumerate(pages, 1)]
        for source, target in files:
            with target.open('xb') as stream:
                stream.write(source.read_bytes())
            created.append(target)
        reports.append(dict(key=key, pages=len(pages), **report))
        print(json.dumps(reports[-1], ensure_ascii=False), flush=True)
    if args.zip:
        with ZipFile(args.out_dir/f'{name}_악보모음.zip', 'x', ZIP_DEFLATED) as z:
            for path in created:
                z.write(path, arcname=path.name)
    (work/'verification.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Completed. Inspect every rendered page visually. Verification: {work / "verification.json"}')


if __name__ == '__main__':
    main()
