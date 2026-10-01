import os,sys,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crm,workqueue
class QueueTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();os.environ['MKX_DATA_FOLDER']=self.tmp.name
 def tearDown(self):self.tmp.cleanup()
 def company(self):
  crm.import_csv(b'title,place_id,website\nClinic,abc,https://example.com\n','j');return crm.list_all()[0]['id']
 def fetch(self,path,limit=None):
  if path.startswith('/api'):return json.dumps([{'ID':'j','Status':'ok'},{'ID':'waiting','Status':'working'}]).encode()
  return b'title,place_id,website\nClinic,abc,https://example.com\n'
 def test_scan_deduplicates_and_imports_completed_only(self):
  workqueue.scan(self.fetch);workqueue.scan(self.fetch)
  self.assertEqual(workqueue.snapshot()['total'],1)
  workqueue.process_one(self.fetch);workqueue.scan(self.fetch)
  self.assertEqual(workqueue.snapshot()['counts']['Concluída'],1)
  self.assertEqual(len(crm.list_all()),1)
 def test_pause_stops_scan_and_claim(self):
  workqueue.enqueue('import','j','import:j');workqueue.settings({'paused':True})
  self.assertIsNone(workqueue.claim());workqueue.scan(self.fetch)
  self.assertEqual(workqueue.snapshot()['total'],1)
 def test_recovery_requeues_interrupted_work(self):
  workqueue.enqueue('import','j');item=workqueue.claim();self.assertEqual(item['attempts'],1)
  workqueue.recover();self.assertEqual(workqueue.snapshot()['counts']['Pendente'],1)
  workqueue.process_one(self.fetch);self.assertEqual(workqueue.snapshot()['items'][0]['attempts'],2)
 def test_fail_retry_and_attempt_limit(self):
  pid=workqueue.enqueue('import','j')
  def bad(*args):raise OSError('Engine unavailable')
  for index in range(3):
   workqueue.process_one(bad)
   self.assertEqual(workqueue.snapshot()['counts']['Falhou'],1)
   if index<2:workqueue.action(pid,'retry')
  with self.assertRaises(ValueError):workqueue.action(pid,'retry')
 def test_batch_skips_blocked_and_missing_sites(self):
  pid=self.company();workqueue.enqueue_companies([pid,pid]);workqueue.enqueue_companies([pid])
  self.assertEqual(workqueue.snapshot()['total'],1)
  crm.update(pid,{'blocked':True});workqueue.process_one()
  self.assertEqual(workqueue.snapshot()['counts']['Cancelada'],1)
  self.assertEqual(workqueue.enqueue_companies([pid])['skipped'],1)
 def test_verification_error_and_blocked_http_are_distinct(self):
  pid=self.company();workqueue.enqueue('verify',pid)
  with patch('crm.verify_site',return_value={'audit':{'site':{'state':'Bloqueado','message':'HTTP 403'}}}):workqueue.process_one()
  self.assertEqual(workqueue.snapshot()['counts']['Concluída'],1)
  workqueue.enqueue('verify',pid)
  with patch('crm.verify_site',return_value={'audit':{'site':{'state':'Erro','message':'Timeout'}}}):workqueue.process_one()
  self.assertEqual(workqueue.snapshot()['counts']['Falhou'],1)
 def test_auto_verify_enqueues_once_after_import(self):
  workqueue.settings({'auto_verify':True});workqueue.scan(self.fetch);workqueue.process_one(self.fetch)
  self.assertEqual(workqueue.snapshot()['counts']['Pendente'],1)
  self.assertEqual(workqueue.snapshot()['total'],2)
 def test_cancel_pending_not_running(self):
  pid=workqueue.enqueue('import','j');workqueue.action(pid,'cancel')
  self.assertIsNone(workqueue.claim());workqueue.action(pid,'retry');workqueue.claim()
  with self.assertRaises(ValueError):workqueue.action(pid,'cancel')
 def test_progress_and_null_jobs(self):
  workqueue.scan(lambda *args:b'null\n');self.assertEqual(workqueue.snapshot()['total'],0)
  workqueue.enqueue('import','j');workqueue.process_one(self.fetch)
  snapshot=workqueue.snapshot();self.assertEqual(snapshot['percent'],100);self.assertEqual(snapshot['treated'],1)
 def test_settings_validation(self):
  with self.assertRaises(ValueError):workqueue.settings({'auto_import':'yes'})
  with self.assertRaises(ValueError):workqueue.settings({'untrusted':True})
if __name__=='__main__':unittest.main()
