#!/usr/bin/env python3
"""Check a filled deck blueprint, provenance references and media arithmetic.

These checks do not verify source truth, realistic rates, strategy or visual quality.
"""
import argparse
import json
import math
from pathlib import Path
import sys

EVIDENCE = {'verified', 'supplied', 'directional', 'assumption', 'proposed'}


def validate(data):
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ['Plan must be a JSON object'], warnings

    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())

    def number(value):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        try:
            return math.isfinite(value)
        except OverflowError:
            return False

    def rows(key):
        value = data.get(key)
        if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
            errors.append(f'{key} must be an array of objects')
            return []
        return value

    def index(items, label):
        result = {}
        for item in items:
            key = item.get('id')
            if not nonempty(key):
                errors.append(f'{label} needs a nonempty id')
            elif key in result:
                errors.append(f'Duplicate {label} id: {key}')
            else:
                result[key] = item
        return result

    def strings(value, label):
        if not isinstance(value, list) or any(not nonempty(x) for x in value):
            errors.append(f'{label} must be an array of nonempty strings')
            return []
        return value

    def close(actual, expected, label, absolute_tolerance=0.5):
        if not number(actual) or abs(actual - expected) > max(absolute_tolerance, abs(expected) * 0.005):
            errors.append(f'{label}: expected approximately {expected:g}, got {actual}')

    meta = data.get('metadata')
    if not isinstance(meta, dict):
        errors.append('metadata must be an object')
        meta = {}
    for key in ('brand', 'objective', 'audience', 'primary_outcome'):
        if not nonempty(meta.get(key)):
            errors.append(f'metadata.{key} is required')

    sources, claims, slides, scenarios, lines = [rows(key) for key in
                                                ('sources', 'claims', 'slides', 'scenarios', 'media_lines')]
    source_by_id = index(sources, 'source')
    claim_by_id = index(claims, 'claim')
    index(slides, 'slide')
    scenario_by_id = index(scenarios, 'scenario')
    index(lines, 'media line')
    if not slides:
        errors.append('At least one slide is required')
    count = meta.get('expected_slide_count')
    if count is not None:
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            errors.append('expected_slide_count must be a positive integer or null')
        elif len(slides) != count:
            errors.append(f'Slide count is {len(slides)}; expected {count} including cover/appendix')

    for source in sources:
        if not nonempty(source.get('label')) or not any(nonempty(source.get(k)) for k in ('url', 'file')):
            errors.append(f"Source {source.get('id')} needs label and url or file")
    for claim in claims:
        label = f"Claim {claim.get('id')}"
        if not nonempty(claim.get('statement')):
            errors.append(f'{label} needs statement')
        kind = claim.get('evidence_type')
        if not isinstance(kind, str) or kind not in EVIDENCE:
            errors.append(f'{label} has invalid evidence_type')
        refs = strings(claim.get('source_ids', []), f'{label}.source_ids')
        for ref in refs:
            if ref not in source_by_id:
                errors.append(f'{label} references missing source {ref}')
        if isinstance(kind, str) and kind in {'verified', 'supplied'} and not refs:
            errors.append(f'{label} needs a source reference')
        if isinstance(kind, str) and kind in {'directional', 'assumption', 'proposed'} and not nonempty(claim.get('basis')):
            errors.append(f'{label} needs a basis/limitation')

    used_claims = set()
    for slide in slides:
        label = f"Slide {slide.get('id')}"
        for key in ('chapter', 'purpose', 'reader_question', 'title', 'takeaway'):
            if not nonempty(slide.get(key)):
                errors.append(f'{label} needs {key}')
        strings(slide.get('body', []), f'{label}.body')
        refs = strings(slide.get('claim_ids', []), f'{label}.claim_ids')
        disclosures = strings(slide.get('disclosures', []), f'{label}.disclosures')
        visual = slide.get('visual')
        if not isinstance(visual, dict) or not nonempty(visual.get('type')):
            errors.append(f'{label} needs visual.type')
        else:
            strings(visual.get('asset_refs', []), f'{label}.visual.asset_refs')
        for ref in refs:
            if ref not in claim_by_id:
                errors.append(f'{label} references missing claim {ref}')
                continue
            used_claims.add(ref)
            kind = claim_by_id[ref].get('evidence_type')
            if isinstance(kind, str) and kind in {'directional', 'assumption', 'proposed'} and not disclosures:
                errors.append(f'{label} needs visible disclosure for claim {ref}')
        if not nonempty(slide.get('transition')):
            warnings.append(f'{label} has no next-slide connection')
    for ref in claim_by_id.keys() - used_claims:
        warnings.append(f'Claim {ref} is not used on a slide')

    totals = {key: 0 for key in scenario_by_id}
    for line in lines:
        label = f"Media line {line.get('id')}"
        scenario_id = line.get('scenario_id')
        if not isinstance(scenario_id, str) or scenario_id not in scenario_by_id:
            errors.append(f'{label} references missing scenario')
        spend = line.get('spend')
        if not number(spend) or spend < 0:
            errors.append(f'{label} needs nonnegative finite spend')
        elif isinstance(scenario_id, str) and scenario_id in totals:
            totals[scenario_id] += spend
        for key in ('rate', 'impressions', 'views', 'clicks', 'conversions', 'unique_reach',
                    'average_frequency', 'ctr', 'cvr'):
            if key in line and (not number(line[key]) or line[key] < 0):
                errors.append(f'{label}.{key} must be a nonnegative finite number')
        for key in ('ctr', 'cvr'):
            if key in line and number(line[key]) and line[key] > 1:
                errors.append(f'{label}.{key} must be a fraction between 0 and 1')
        model = line.get('cost_model')
        if not isinstance(model, str) or model not in {'CPM', 'CPV', 'CPC', 'CPA', 'FIXED'}:
            errors.append(f'{label} needs cost_model CPM, CPV, CPC, CPA or FIXED')
        if isinstance(model, str) and model in {'CPM', 'CPV', 'CPC', 'CPA'}:
            rate = line.get('rate')
            if not number(rate) or rate <= 0:
                errors.append(f'{label} needs a positive finite rate')
            elif number(spend) and spend >= 0:
                metric, multiplier = {'CPM': ('impressions', 1000), 'CPV': ('views', 1),
                                      'CPC': ('clicks', 1), 'CPA': ('conversions', 1)}[model]
                if metric not in line:
                    errors.append(f'{label} needs {metric} for {model} checking')
                else:
                    close(line[metric], spend / rate * multiplier, f'{label}.{metric}')
        for result, base, fraction in [('clicks', 'impressions', 'ctr'), ('conversions', 'clicks', 'cvr')]:
            if all(key in line and number(line[key]) for key in (result, base, fraction)):
                close(line[result], line[base] * line[fraction], f'{label}.{result}')
        if 'average_frequency' in line:
            reach, impressions = line.get('unique_reach'), line.get('impressions')
            if not number(reach) or reach <= 0 or not number(impressions):
                errors.append(f'{label} frequency needs positive unique_reach and impressions')
            elif not nonempty(line.get('reach_scope')) or line.get('reach_scope') != line.get('impression_scope'):
                errors.append(f'{label} frequency needs matching reach_scope and impression_scope')
            else:
                close(line['average_frequency'], impressions / reach, f'{label}.average_frequency', 0.01)
    for scenario_id, scenario in scenario_by_id.items():
        amount = scenario.get('media_budget')
        if not number(amount) or amount < 0:
            errors.append(f'Scenario {scenario_id} needs nonnegative finite media_budget')
        else:
            close(totals[scenario_id], amount, f'Scenario {scenario_id} media spend total')
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.plan.read_text(encoding='utf-8'))
        errors, warnings = validate(data)
    except (OSError, ValueError, OverflowError) as exc:
        errors, warnings = [str(exc)], []
    for message in warnings:
        print(f'WARNING: {message}')
    for message in errors:
        print(f'ERROR: {message}')
    print(f'{len(errors)} error(s), {len(warnings)} warning(s). Checks are structural and arithmetic only.')
    return bool(errors)


if __name__ == '__main__':
    sys.exit(main())
