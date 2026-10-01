import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import crm

class IntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();os.environ['MKX_DATA_FOLDER']=self.tmp.name
        crm.import_csv(b'title,place_id,phone\nClinic,abc,123\n','job')
        self.pid=crm.list_all()[0]['id']
    def tearDown(self):self.tmp.cleanup()
    def review(self, **answers):
        return crm.save_review(self.pid, {'answers':answers,'evidence':'https://example.com consultado; oportunidade e contexto conferidos.'})
    def test_unreviewed_missing_site_is_not_priority(self):
        item=crm.audit(self.pid)
        self.assertEqual(item['intelligence']['score'],0)
        self.assertEqual(item['intelligence']['priority'],'Revisão pendente')
    def test_confirmed_and_contact_fit_explain_score(self):
        result=self.review(site_gap='Confirmado',contact_fit='Confirmado')['intelligence']
        self.assertEqual(result['score'],55)
        self.assertEqual(result['priority'],'Prioritária')
        self.assertEqual(sum(r['points'] for r in result['reasons']),55)
        self.assertEqual(result['services'],['Site institucional'])
    def test_block_always_overrides_score(self):
        self.review(site_gap='Confirmado',contact_fit='Confirmado')
        item=crm.update(self.pid,{'blocked':True})
        self.assertEqual(item['intelligence']['priority'],'Não contatar')
        self.assertEqual(item['intelligence']['score'],0)
    def test_review_persists_but_becomes_stale_when_data_changes(self):
        self.review(site_gap='Confirmado')
        crm.import_csv(b'title,place_id,phone\nClinic,abc,456\n','job2')
        result=crm.get(self.pid)['intelligence']
        self.assertEqual(result['review_state'],'Desatualizada')
        self.assertEqual(result['score'],0)
        self.assertIn('https://',result['review']['evidence'])
    def test_identical_import_and_stage_change_keep_review(self):
        self.review(conversion_gap='Confirmado')
        crm.import_csv(b'title,place_id,phone\nClinic,abc,123\n','job')
        item=crm.update(self.pid,{'stage':'Em análise'})
        self.assertEqual(item['intelligence']['review_state'],'Atualizada')
        self.assertEqual(item['intelligence']['priority'],'Qualificar contato')
    def test_evidence_and_enum_validation(self):
        with self.assertRaises(ValueError):crm.save_review(self.pid,{'answers':{'site_gap':'Confirmado'},'evidence':'curto'})
        with self.assertRaises(ValueError):self.review(unknown='Confirmado')
        with self.assertRaises(ValueError):self.review(site_gap='sim')
    def test_site_change_stales_review_but_timestamp_does_not(self):
        import json
        with crm.connect() as db:db.execute('UPDATE prospects SET audit=? WHERE id=?',(json.dumps({'site':{'state':'Verificado','at':'one'}}),self.pid))
        self.review(site_gap='Descartado')
        with crm.connect() as db:db.execute('UPDATE prospects SET audit=? WHERE id=?',(json.dumps({'site':{'state':'Verificado','at':'two'}}),self.pid))
        self.assertEqual(crm.get(self.pid)['intelligence']['review_state'],'Atualizada')
        with crm.connect() as db:db.execute('UPDATE prospects SET audit=? WHERE id=?',(json.dumps({'site':{'state':'Bloqueado'}}),self.pid))
        self.assertEqual(crm.get(self.pid)['intelligence']['review_state'],'Desatualizada')

if __name__=='__main__':unittest.main()
