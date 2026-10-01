import os,sys,tempfile,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crm,relationship
class RelationshipTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();os.environ['MKX_DATA_FOLDER']=self.tmp.name
  crm.import_csv(b'title,place_id\nCompany,abc\n','j');self.pid=crm.list_all()[0]['id']
 def tearDown(self):self.tmp.cleanup()
 def task(self):return relationship.save_task({'company':self.pid,'title':'Revisar contato','due':'2026-01-01T12:00:00-03:00','notes':'Contexto'})
 def event(self,kind='Resposta recebida',pid=None):return {'id':pid or uuid.uuid4().hex,'company':self.pid,'kind':kind,'channel':'E-mail','notes':'Registro da resposta recebida.'}
 def test_due_timezone_and_overdue(self):
  task=self.task();self.assertEqual(task['due'],'2026-01-01T15:00:00+00:00');self.assertTrue(task['overdue'])
  with self.assertRaises(ValueError):relationship.due_value('2026-01-01T12:00:00')
 def test_completion_and_conflict(self):
  task=self.task();new=relationship.save_task({**task,'status':'Concluída'})
  self.assertFalse(new['overdue']);self.assertEqual(new['revision'],2)
  with self.assertRaises(ValueError):relationship.save_task({**task,'status':'Cancelada'})
 def test_optout_blocks_and_cancels_tasks_atomically(self):
  self.task();relationship.log_interaction(self.event('Recusa / descadastro'))
  self.assertTrue(crm.get(self.pid)['blocked']);self.assertEqual(relationship.tasks()[0]['status'],'Cancelada')
  with self.assertRaises(ValueError):self.task()
 def test_block_via_crm_also_cancels_tasks(self):
  self.task();crm.update(self.pid,{'blocked':True})
  self.assertEqual(relationship.tasks()[0]['status'],'Cancelada')
 def test_manual_record_idempotent(self):
  body=self.event();relationship.log_interaction(body);relationship.log_interaction(body)
  self.assertEqual(len(relationship.interactions(self.pid)),1)
  with self.assertRaises(ValueError):relationship.log_interaction({**body,'notes':'Outro texto'})
 def test_draft_requires_review_and_respects_block(self):
  with self.assertRaises(ValueError):relationship.draft(self.pid,'E-mail')
  crm.save_review(self.pid,{'answers':{'conversion_gap':'Confirmado','contact_fit':'Confirmado'},'evidence':'Fontes de conversão e canal institucional revisados.'})
  self.assertIn('conversão',relationship.draft(self.pid,'WhatsApp')['body'])
  crm.update(self.pid,{'blocked':True})
  with self.assertRaises(ValueError):relationship.draft(self.pid,'E-mail')
 def test_reimport_preserves_tasks_and_records(self):
  self.task();relationship.log_interaction(self.event())
  crm.import_csv(b'title,place_id\nCompany,abc\n','j2')
  self.assertEqual(len(relationship.tasks()),1);self.assertEqual(len(relationship.interactions(self.pid)),1)
if __name__=='__main__':unittest.main()
