"""Static breakpoint contracts, NOT a CSS layout/cascade engine or browser test.

Inspect declarations for named selectors in the actual stylesheet at boundary
widths. Geometry, clipping, native media queries and keyboard behavior need a
browser. No dependency installation, external resource or listener is involved.
"""
from pathlib import Path
import re
import unittest

CSS = Path(__file__).resolve().parents[1] / 'static/style.css'


def blocks(source):
    """Read the stylesheet's balanced rule/media blocks (no quoted braces used)."""
    source = re.sub(r'/\*.*?\*/', '', source, flags=re.S)
    pos = 0
    while pos < len(source):
        start = source.find('{', pos)
        if start == -1:
            assert not source[pos:].strip(), 'Unparsed CSS tail'
            break
        depth, end = 1, start + 1
        while depth and end < len(source):
            depth += (source[end] == '{') - (source[end] == '}')
            end += 1
        assert depth == 0, 'Unclosed CSS block'
        yield source[pos:start].strip(), source[start + 1:end - 1]
        pos = end


def declarations(selector, width, source=None):
    """Last declarations for this exact selector; deliberately not full cascade."""
    result = {}
    for head, body in blocks(CSS.read_text() if source is None else source):
        if head.startswith('@media'):
            query = re.fullmatch(r'@media\s*\((min|max)-width:\s*(\d+)px\)', head)
            if query:
                bound = int(query[2])
                if (width <= bound if query[1] == 'max' else width >= bound):
                    result.update(declarations(selector, width, body))
        elif selector in [part.strip() for part in head.split(',')]:
            for declaration in body.split(';'):
                if declaration.strip():
                    key, value = declaration.split(':', 1)
                    result[key.strip()] = value.strip()
    return result


class ResponsiveContractTests(unittest.TestCase):
    def test_coverage_and_grid_switch_at_tablet_boundary(self):
        for width in (320, 390, 760, 761, 1100):
            with self.subTest(width=width):
                self.assertEqual(declarations('#data-coverage', width)['grid-template-columns'], '1fr')
                self.assertEqual(declarations('.admin-layout .grid', width)['grid-template-columns'], '1fr')
        for width in (1101, 1350, 1920):
            self.assertEqual(declarations('#data-coverage', width)['grid-template-columns'], 'repeat(3,minmax(0,1fr))')
            self.assertEqual(declarations('.admin-layout .grid', width)['grid-template-columns'], 'minmax(0,1fr) minmax(0,1fr)')

    def test_mobile_navigation_releases_sidebar_space(self):
        for width in (320, 390, 760):
            with self.subTest(width=width):
                self.assertEqual(declarations('.sidebar', width)['position'], 'static')
                self.assertEqual(declarations('.sidebar', width)['width'], 'auto')
                self.assertEqual(declarations('.admin-layout>main', width)['margin-left'], '0')
                self.assertEqual(declarations('.workspace-nav', width)['grid-template-columns'], 'repeat(2,minmax(0,1fr))')
                self.assertEqual(declarations('.workspace-toolbar', width)['flex-direction'], 'column')
                self.assertEqual(declarations('.filter-field', width)['flex-basis'], '100%')
        self.assertEqual(declarations('.sidebar', 761)['position'], 'fixed')
        self.assertNotIn('flex-direction', declarations('.workspace-toolbar', 761))

    def test_wide_roster_and_local_table_overflow(self):
        self.assertNotIn('grid-template-columns', declarations('.admin-layout .roster-grid', 1349))
        self.assertEqual(declarations('.admin-layout .roster-grid', 1350)['grid-template-columns'], 'minmax(0,1.6fr) minmax(300px,1fr)')
        self.assertEqual(declarations('.gap-comparison', 390)['overflow-x'], 'auto')
        self.assertEqual(declarations('.admin-layout .gap-comparison table', 390)['min-width'], 'calc(var(--gap-columns,3) * 180px)')
        self.assertEqual(declarations('.admin-layout .gap-comparison table', 390)['table-layout'], 'fixed')
        self.assertEqual(declarations('.workspace-nav a', 390)['overflow-wrap'], 'anywhere')
        self.assertEqual(declarations('.filter-bar', 390)['flex-wrap'], 'wrap')
        self.assertEqual(declarations('.admin-layout .panel', 390)['min-width'], '0')


if __name__ == '__main__':
    unittest.main()
