"""Test provenance, media arithmetic, PPTX ordering and non-destructive installation."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'marketing-pitch-deck-skill'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


plan_tool = module('plan_tool', SKILL / 'scripts/validate_plan.py')
pptx_tool = module('pptx_tool', SKILL / 'scripts/inspect_pptx.py')
project_tool = module('project_tool', SKILL / 'scripts/init_project.py')
installer = module('installer', ROOT / 'tools/install_skill.py')


class PlanChecks(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / 'examples/sample-plan.json').read_text())

    def test_valid_example(self):
        self.assertEqual(plan_tool.validate(self.plan), ([], []))

    def test_missing_source_and_claim(self):
        self.plan['claims'][0]['source_ids'] = ['missing']
        self.plan['slides'][0]['claim_ids'] = ['missing']
        errors, _ = plan_tool.validate(self.plan)
        self.assertTrue(any('missing source' in x for x in errors))
        self.assertTrue(any('missing claim' in x for x in errors))

    def test_uncertainty_needs_visible_disclosure(self):
        self.plan['slides'][2]['disclosures'] = []
        errors, _ = plan_tool.validate(self.plan)
        self.assertTrue(any('visible disclosure' in x for x in errors))

    def test_budget_and_rate_math(self):
        self.plan['media_lines'][0]['spend'] = 310000
        errors, _ = plan_tool.validate(self.plan)
        self.assertTrue(any('impressions' in x for x in errors))
        self.assertTrue(any('media spend total' in x for x in errors))

    def test_percentages_are_fractions(self):
        self.plan['media_lines'][0]['ctr'] = 5
        errors, _ = plan_tool.validate(self.plan)
        self.assertTrue(any('fraction between' in x for x in errors))

    def test_bad_frequency_scope(self):
        self.plan['media_lines'][0]['reach_scope'] = 'different-period'
        errors, _ = plan_tool.validate(self.plan)
        self.assertTrue(any('matching reach_scope' in x for x in errors))

    def test_frequency_arithmetic(self):
        self.plan['media_lines'][0]['average_frequency'] = 3.4
        errors, _ = plan_tool.validate(self.plan)
        self.assertTrue(any('average_frequency: expected' in x for x in errors))

    def test_invalid_numeric_inputs(self):
        for invalid in (0, -1, float('nan'), float('inf'), 10 ** 500, True, '100'):
            with self.subTest(invalid=invalid):
                plan = deepcopy(self.plan)
                plan['media_lines'][0]['rate'] = invalid
                self.assertTrue(plan_tool.validate(plan)[0])

    def test_count_and_duplicate_ids(self):
        self.plan['metadata']['expected_slide_count'] = 18
        self.plan['slides'][1]['id'] = '01'
        errors, _ = plan_tool.validate(self.plan)
        self.assertTrue(any('Slide count' in x for x in errors))
        self.assertTrue(any('Duplicate slide' in x for x in errors))

    def test_invalid_structures_do_not_crash(self):
        for invalid in (None, [], {'metadata': [], 'slides': 'text'}):
            self.assertTrue(plan_tool.validate(invalid)[0])
        self.plan['claims'][0]['evidence_type'] = []
        self.plan['media_lines'][0]['cost_model'] = {}
        self.plan['media_lines'][0]['scenario_id'] = []
        self.assertTrue(plan_tool.validate(self.plan)[0])

    def test_cli_returns_nonzero_for_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text('{bad json')
            result = subprocess.run([sys.executable, str(SKILL / 'scripts/validate_plan.py'), str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('ERROR:', result.stdout)


class ProjectAndInstallChecks(unittest.TestCase):
    def test_init_preserves_existing_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'project'
            project_tool.initialize(dest)
            brief = dest / 'brief-template.md'
            brief.write_text('Approved client work')
            with self.assertRaises(ValueError):
                project_tool.initialize(dest)
            self.assertEqual(brief.read_text(), 'Approved client work')
            self.assertTrue((dest / 'research/source-ledger.csv').is_file())

    def test_installer_refuses_then_backs_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / '.agents/skills/marketing-pitch-deck-skill'
            backup_root = base / '.agents/skill-backups'
            installer.install(SKILL, target, backup_root)
            (target / 'SKILL.md').write_text('Customized old version')
            with self.assertRaises(ValueError):
                installer.install(SKILL, target, backup_root)
            backup = installer.install(SKILL, target, backup_root, force=True)
            self.assertEqual((backup / 'SKILL.md').read_text(), 'Customized old version')
            self.assertEqual((target / 'SKILL.md').read_bytes(), (SKILL / 'SKILL.md').read_bytes())
            self.assertFalse(any(x.name.startswith('staging-') for x in backup_root.iterdir()))

    def test_project_cli_installs_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, str(ROOT / 'tools/install_skill.py'),
                                    '--agent', 'both', '--scope', 'project', '--project-dir', tmp],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for folder in ('.agents', '.claude'):
                self.assertTrue((Path(tmp) / folder / 'skills/marketing-pitch-deck-skill/SKILL.md').is_file())


class PresentationChecks(unittest.TestCase):
    def test_actual_slide_order_and_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'synthetic-structure.pptx'
            # Minimal structural fixture, not a complete application-ready PPTX.
            with ZipFile(path, 'w') as archive:
                archive.writestr('ppt/presentation.xml', '''<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="r2"/><p:sldId id="257" r:id="r1"/></p:sldIdLst><p:sldSz cx="1000" cy="1000"/></p:presentation>''')
                archive.writestr('ppt/_rels/presentation.xml.rels', '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Target="slides/slide1.xml"/><Relationship Id="r2" Target="slides/slide2.xml"/></Relationships>''')
                for number, text, x in ((1, 'Second', 0), (2, 'First', -20)):
                    archive.writestr(f'ppt/slides/slide{number}.xml', f'''<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree><p:sp><p:spPr><a:xfrm><a:off x="{x}" y="0"/><a:ext cx="200" cy="200"/></a:xfrm></p:spPr><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>''')
            result = pptx_tool.inspect(path, 2)
            self.assertEqual([s['text'][0] for s in result['slides']], ['First', 'Second'])
            self.assertEqual(result['slides'][0]['text_shapes'], 1)
            self.assertEqual(len(result['slides'][0]['out_of_canvas_objects']), 1)
            with self.assertRaises(ValueError):
                pptx_tool.inspect(path, 3)


if __name__ == '__main__':
    unittest.main()
