import os,sys,tempfile,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crm,sales,relationship,results
class ResultsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();os.environ['MKX_DATA_FOLDER']=self.tmp.name
  crm.import_csv(b'title,place_id\nClient,abc\n','j');self.pid=crm.list_all()[0]['id']
 def tearDown(self):self.tmp.cleanup()
 def receipt(self,**kw):
  body={'id':uuid.uuid4().hex,'company':self.pid,'kind':'Recebimento','amount':'100.25','day':'2020-01-01','reference':uuid.uuid4().hex,'confirmed':True};body.update(kw);return results.save_receipt(body)
 def snapshot(self):return results.snapshot('2020-01-01','2020-01-31')
 def test_empty_and_current_portfolio(self):
  s=self.snapshot();self.assertEqual(s['portfolio']['companies'],1);self.assertEqual(s['cash']['net'],0)
  self.assertEqual(s['proposals']['total'],0);self.assertEqual(s['activity']['records'],0)
 def test_accepted_values_do_not_become_cash(self):
  crm.save_review(self.pid,{'answers':{'site_gap':'Confirmado'},'evidence':'Site revisado com fonte e contexto registrados.'})
  body={'company':self.pid,'status':'Aceita registrada','lines':[{'name':'Site','scope':'Entrega','price':'2500','billing':'Único'},{'name':'Gestão','scope':'Mensal','price':'300','billing':'Mensal'}],'terms':'Pagamento acordado.','deadline':'15 dias','evidence':'Contexto revisado com fontes da oportunidade.'}
  p=sales.save_proposal(body);body.update(id=p['id'],revision=p['revision']);sales.save_proposal(body)
  s=self.snapshot();self.assertEqual(s['proposals']['accepted'],1);self.assertEqual(s['proposals']['accepted_one_time'],250000);self.assertEqual(s['proposals']['accepted_monthly'],30000);self.assertEqual(s['cash']['gross'],0)
 def test_idempotence_and_duplicate_reference(self):
  pid=uuid.uuid4().hex;r=self.receipt(id=pid,reference='bank-ref')
  repeat=self.receipt(id=pid,reference='bank-ref');self.assertEqual(r['id'],repeat['id']);self.assertEqual(len(results.receipts()),1)
  with self.assertRaises(ValueError):self.receipt(reference='bank-ref')
  with self.assertRaises(ValueError):self.receipt(id=pid,reference='bank-ref',amount='500')
 def test_refunds_and_void_keep_audit(self):
  receipt=self.receipt();self.receipt(kind='Estorno',amount='20')
  self.assertEqual(self.snapshot()['cash']['net'],8025)
  results.void_receipt(receipt['id'],'Valor lançado na empresa incorreta.')
  s=self.snapshot();self.assertEqual(s['cash']['gross'],0);self.assertEqual(s['cash']['net'],-2000);self.assertEqual(len(s['receipts']),2);self.assertTrue(next(r for r in s['receipts'] if r['id']==receipt['id'])['voided'])
 def test_period_and_fortaleza_unique_activity(self):
  for _ in range(2):relationship.log_interaction({'id':uuid.uuid4().hex,'company':self.pid,'kind':'Contato realizado','channel':'E-mail','notes':'Contato registrado.'})
  with crm.connect() as db:db.execute("UPDATE interactions SET at='2020-01-02T01:00:00+00:00'")
  s=results.snapshot('2020-01-01','2020-01-01');self.assertEqual(s['activity']['contacted_companies'],1);self.assertEqual(s['activity']['records'],2)
  self.assertEqual(results.snapshot('2020-01-02','2020-01-02')['activity']['records'],0)
 def test_future_and_confirmation_and_period_validation(self):
  with self.assertRaises(ValueError):self.receipt(day='2999-01-01')
  with self.assertRaises(ValueError):self.receipt(confirmed=False)
  with self.assertRaises(ValueError):self.receipt(amount='0')
  with self.assertRaises(ValueError):results.snapshot('2021-01-01','2020-01-01')
 def test_proposal_link_company_checked_and_blocked_history_allowed(self):
  crm.import_csv(b'title,place_id\nOther,xyz\n','j');other=next(i['id'] for i in crm.list_all() if i['id']!=self.pid)
  p=sales.save_proposal({'company':other,'lines':[{'name':'Site','scope':'Entrega','price':'100','billing':'Único'}]})
  with self.assertRaises(ValueError):self.receipt(proposal=p['id'])
  crm.update(self.pid,{'blocked':True});self.receipt();self.assertEqual(self.snapshot()['cash']['gross'],10025)
 def test_export_formula_protection(self):
  self.receipt(reference='=HYPERLINK()',notes='@formula')
  csv=results.export('2020-01-01','2020-01-31').decode();self.assertIn("'=HYPERLINK()",csv);self.assertIn("'@formula",csv)
if __name__=='__main__':unittest.main()
