import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crm
import sales

class SalesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();os.environ['MKX_DATA_FOLDER']=self.tmp.name
        crm.import_csv(b'title,place_id\nCompany,abc\n','j');self.pid=crm.list_all()[0]['id']
    def tearDown(self):self.tmp.cleanup()
    def body(self):
        return {'company':self.pid,'lines':[{'name':'Site','scope':'Uma página','conditions':'Conteúdo fornecido','price':'2500.00','billing':'Único'},{'name':'Gestão','scope':'Mensal','price':'350.50','billing':'Mensal'}],'evidence':'Contexto revisado e fontes identificadas.','terms':'Pagamento e validade definidos.','deadline':'15 dias após acessos.'}
    def test_default_catalog_and_deactivation(self):
        self.assertEqual(len(sales.catalog()),6)
        item=sales.catalog()[0];item['active']=False;item['price']='2000,00';sales.save_service(item)
        match=next(s for s in sales.catalog() if s['id']==item['id'])
        self.assertFalse(match['active']);self.assertEqual(match['price'],'2000.00')
    def test_exact_money_and_validation(self):
        self.assertEqual(sales.money('0.29'),29)
        for value in ('NaN','Infinity','-1','1.234','10000001','abc'):
            with self.assertRaises(ValueError):sales.money(value)
    def test_totals_and_snapshots_survive_catalog_change(self):
        p=sales.save_proposal(self.body())
        self.assertEqual(p['one_time_cents'],250000);self.assertEqual(p['monthly_cents'],35050)
        service=sales.catalog()[0];service['price']='999';sales.save_service(service)
        self.assertEqual(sales.proposal(p['id'])['one_time_cents'],250000)
    def test_revisions_history_and_conflict(self):
        body=self.body();first=sales.save_proposal(body);body.update(id=first['id'],revision=first['revision']);body['lines'][0]['price']='3000';second=sales.save_proposal(body)
        self.assertEqual(second['revision'],2);self.assertEqual(len(second['history']),2)
        self.assertEqual(sales.proposal(first['id'],1)['one_time_cents'],250000)
        with self.assertRaises(ValueError):sales.save_proposal(body)
    def test_ready_requires_review_prices_and_terms(self):
        body=self.body();body['status']='Pronta'
        with self.assertRaises(ValueError):sales.save_proposal(body)
        crm.save_review(self.pid,{'answers':{'site_gap':'Confirmado'},'evidence':'Site não encontrado após revisão com fontes registradas.'})
        self.assertEqual(sales.save_proposal(body)['status'],'Pronta')
        body['lines'][0]['price']='0'
        with self.assertRaises(ValueError):sales.save_proposal(body)
    def test_blocked_company_and_company_change(self):
        p=sales.save_proposal(self.body())
        crm.update(self.pid,{'blocked':True})
        with self.assertRaises(ValueError):sales.save_proposal(self.body())
        crm.import_csv(b'title,place_id\nOther,xyz\n','j')
        pid=next(i['id'] for i in crm.list_all() if i['data']['title']=='Other')
        body=self.body();body.update(id=p['id'],revision=1,company=pid)
        with self.assertRaises(ValueError):sales.save_proposal(body)
    def test_print_escapes_content_and_separates_monthly(self):
        body=self.body();body['evidence']='<script>alert(1)</script>'
        p=sales.save_proposal(body);html=sales.render(p['id']).decode()
        self.assertNotIn('<script>',html);self.assertIn('&lt;script&gt;',html)
        self.assertIn('R$ 2.500,00',html);self.assertIn('R$ 350,50',html);self.assertIn('window.print()',html)

if __name__=='__main__':unittest.main()
