"""Static naming/reference audit only, not a browser or accessibility certification."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children, self.parts = [], []

    def text(self):
        return ' '.join(self.parts + [child.text() for child in self.children]).strip()

    def ancestors(self):
        node = self.parent
        while node:
            yield node
            node = node.parent

    def descendants(self):
        for child in self.children:
            yield child
            yield from child.descendants()


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.root = Node('root', [])
        self.stack, self.nodes = [self.root], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, text):
        self.stack[-1].parts.append(text)


class CardMarkupTests(unittest.TestCase):
    def setUp(self):
        self.document = Document((ROOT/'static/index.html').read_text())
        self.nodes = self.document.nodes
        self.by_id = {n.attrs['id']: n for n in self.nodes if 'id' in n.attrs}

    def test_ids_references_labels_and_card_headings(self):
        ids = [n.attrs['id'] for n in self.nodes if 'id' in n.attrs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(n.tag == 'html' and n.attrs.get('lang') for n in self.nodes))
        labels = {n.attrs['for']: n.text() for n in self.nodes if n.tag == 'label' and 'for' in n.attrs}
        for node in self.nodes:
            for attr in ('aria-labelledby', 'aria-describedby', 'aria-controls'):
                for target in node.attrs.get(attr, '').split():
                    self.assertIn(target, self.by_id, (node.attrs, attr))
            if node.tag == 'label' and 'for' in node.attrs:
                self.assertIn(node.attrs['for'], self.by_id)
            self.assertLessEqual(int(node.attrs.get('tabindex', 0)), 0)
            if node.tag in ('button', 'input', 'select', 'textarea') and node.attrs.get('type') != 'hidden':
                name = node.attrs.get('aria-label', '').strip()
                name = name or ' '.join(self.by_id[t].text() for t in node.attrs.get('aria-labelledby', '').split())
                name = name or labels.get(node.attrs.get('id'), '')
                name = name or ' '.join(p.text() for p in node.ancestors() if p.tag == 'label')
                name = name or (node.text() if node.tag == 'button' else '')
                self.assertTrue(name.strip(), (node.tag, node.attrs))
            if node.tag == 'section' and 'panel' in node.attrs.get('class', '').split():
                self.assertTrue(any(child.tag in ('h1', 'h2', 'h3', 'h4') and child.text()
                                    for child in node.descendants()), node.attrs)

    def test_async_results_and_login_errors_have_announcement_markup(self):
        self.assertEqual(self.by_id['error'].attrs.get('role'), 'alert')
        for identity in ('hub-trace', 'hub-health', 'interaction-status', 'bridge-status', 'ffxi-focus-bridge'):
            attrs = self.by_id[identity].attrs
            self.assertTrue(attrs.get('aria-live') == 'polite' or attrs.get('role') == 'status', identity)

    def test_enb_handoff_is_dated_read_only_operations_context(self):
        panel = self.by_id['enb-deployment']
        self.assertIn(self.by_id['view-operations'], list(panel.ancestors()))
        text = panel.text()
        for value in ('37.27.113.160', 'enb.bansheerealm.com', '5:29 PM CT',
                      'Coordinator-reported', 'Unknown', 'rollback', 'reported stopped'):
            self.assertIn(value, text)
        self.assertFalse(any(n.tag in ('a', 'button', 'input', 'form') for n in panel.descendants()))

    def test_ax41_retirement_keeps_reported_dependency_separate_from_completion(self):
        panel = self.by_id['ax41-retirement']
        self.assertIn(self.by_id['view-operations'], list(panel.ancestors()))
        text = panel.text()
        for value in ('trinitycore', '5:45 PM CT', 'WoW Forever wake controller',
                      'still routed through AX41', 'Retirement completion:', 'Unknown',
                      'does not establish that every AX41 dependency has moved'):
            self.assertIn(value, text)
        self.assertFalse(any(n.tag in ('a', 'button', 'input', 'form') for n in panel.descendants()))

    def test_bridge_and_stackd_cards_keep_dated_evidence_limits(self):
        for identity in ('dit-r2-deployment', 'stackd-drift'):
            panel = self.by_id[identity]
            self.assertIn(self.by_id['view-operations'], list(panel.ancestors()))
            self.assertFalse(any(n.tag in ('a', 'button', 'input', 'form') for n in panel.descendants()))
        bridge = self.by_id['dit-r2-deployment'].text()
        for value in ('9ba4ccb', 'ce66285', '22:53:01 UTC', 'Audit errors: 0',
                      'Polls: 1', 'input rows: 0', 'hub rows: 0', 'queue rows: 0',
                      'Not exercised', 'values Unknown', 'not observed',
                      '6ad8732c', '22:56:51 UTC', 'ALIVE_CHATTER=1', '35f7d587'):
            self.assertIn(value, bridge)
        drift = self.by_id['stackd-drift'].text()
        for value in ('Blind restart unsafe', 'STACKD_GAMES', ',ffxi',
                      'de8c612', '22:56:28 UTC', 'daemon-reload only',
                      'Saved set after reload (4)', 'Unchanged running set (6)',
                      'tabula-rasa', 'war, planetside, rose', '8446/8450', 'Unknown'):
            self.assertIn(value, drift)
        self.assertNotIn('persisted: 5', drift)
        self.assertNotIn('still ends', drift)

    def test_model_and_operational_controls_remain_disabled(self):
        for identity in ('global-model', 'global-model-toggle'):
            node = self.by_id[identity]
            self.assertTrue('disabled' in node.attrs or any(
                p.tag == 'fieldset' and 'disabled' in p.attrs for p in node.ancestors()), identity)
        stop_buttons = [n for n in self.nodes if n.tag == 'button' and n.text().startswith('Stop ')]
        self.assertEqual(len(stop_buttons), 2)
        for node in stop_buttons:
            self.assertTrue(any(p.tag == 'fieldset' and 'disabled' in p.attrs for p in node.ancestors()))
