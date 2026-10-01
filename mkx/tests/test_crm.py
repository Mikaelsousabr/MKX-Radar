import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import crm

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ['MKX_DATA_FOLDER'] = self.tmp.name
    def tearDown(self):
        self.tmp.cleanup()
    def sample(self, address='Rua A', pid='p1'):
        return f'title,address,place_id,phone,website\nClínica,{address},{pid},88999999999,\n'.encode()
    def test_reimport_preserves_block_notes_sources(self):
        self.assertEqual(crm.import_csv(self.sample(), 'job1')['added'], 1)
        item = crm.list_all()[0]
        crm.update(item['id'], {'blocked': True, 'notes': 'Pediu para não receber contato'})
        self.assertEqual(crm.import_csv(self.sample('Rua nova'), 'job2')['updated'], 1)
        item = crm.get(item['id'])
        self.assertEqual(item['data']['address'], 'Rua nova')
        self.assertTrue(item['blocked'])
        self.assertEqual(item['stage'], 'Não contatar')
        self.assertEqual(len(item['sources']), 2)
        self.assertIn('Pediu', item['notes'])
        with self.assertRaises(ValueError): crm.draft(item['id'])
        with self.assertRaises(ValueError): crm.update(item['id'], {'blocked': False, 'stage': 'Identificada'})
    def test_branches_do_not_merge_by_phone(self):
        crm.import_csv(self.sample('Rua A', ''), 'j')
        crm.import_csv(self.sample('Rua B', ''), 'j')
        self.assertEqual(len(crm.list_all()), 2)
    def test_bad_csv_and_stage(self):
        with self.assertRaises(ValueError): crm.import_csv(b'foo,bar\na,b\n', 'j')
        crm.import_csv(self.sample(), 'j')
        with self.assertRaises(ValueError): crm.update(crm.list_all()[0]['id'], {'stage': 'inválida'})
    def test_audit_evidence_and_draft(self):
        crm.import_csv(self.sample(), 'j')
        item = crm.audit(crm.list_all()[0]['id'])
        self.assertIn('Confirmar', item['audit']['findings'][0]['observation'])
        self.assertIn('não comprova', item['audit']['limitations'])
        self.assertIn('sem envio', crm.draft(item['id'])['warning'])
        self.assertTrue(item['history'])

if __name__ == '__main__': unittest.main()

class InterfaceTests(unittest.TestCase):
    def test_completed_actions_and_removed_links(self):
        import gateway
        fragment=b'<tr><td><span class="status-indicator status-ok">ok</span><a href="/download?id=abc-123">Download</a></td></tr>'
        result=gateway.transform_html(fragment).decode()
        self.assertIn('/empresas?job=abc-123&amp;view=analysis', result)
        self.assertIn('Analisar', result)
        pending=fragment.replace(b'status-ok',b'status-working')
        self.assertNotIn('view=analysis',gateway.transform_html(pending).decode())
        for file in ('index.html','crm.html'):
            html=(Path(__file__).resolve().parents[1]/file).read_text()
            self.assertNotIn('href="/original/"',html)
            self.assertNotIn('href="/api/docs"',html)
            self.assertIn('Mapa interativo',html)
    def test_repeat_import_preserves_analysis(self):
        with tempfile.TemporaryDirectory() as folder:
            os.environ['MKX_DATA_FOLDER']=folder
            payload=b'title,place_id\nTeste,stable\n'
            crm.import_csv(payload,'j')
            pid=crm.list_all()[0]['id']
            crm.audit(pid)
            crm.import_csv(payload,'j')
            self.assertTrue(crm.get(pid)['audit']['findings'])
