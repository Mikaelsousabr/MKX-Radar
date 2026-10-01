import os,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crm,localai,gateway
class LocalAITests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();os.environ['MKX_DATA_FOLDER']=self.tmp.name
 def tearDown(self):self.tmp.cleanup()
 def models(self):return {'models':[{'name':'model:local','size':1234},{'name':'other:cloud','remote_host':'remote'}]}
 def test_lists_local_models_only(self):
  with patch('localai.request',return_value=self.models()):self.assertEqual([m['name'] for m in localai.status()['models']],['model:local'])
 def test_save_persists_and_disable_overrides_env(self):
  with patch('localai.request',return_value=self.models()):localai.save('model:local')
  self.assertEqual(localai.selected(),'model:local')
  with patch.dict(os.environ,{'MKX_OLLAMA_MODEL':'model:old'}):
   localai.save('');self.assertEqual(localai.selected(),'')
 def test_unknown_model_and_unavailable_connection(self):
  with patch('localai.request',return_value=self.models()):
   with self.assertRaises(ValueError):localai.save('unknown')
  with patch('localai.request',side_effect=ValueError('Ollama indisponível')):self.assertFalse(localai.status()['connected'])
 def test_generation_uses_selected_model(self):
  with patch('localai.request',return_value=self.models()):localai.save('model:local')
  def request(path,body=None,timeout=8):
   if path=='/api/tags':return self.models()
   self.assertEqual(body['model'],'model:local');self.assertEqual(timeout,120);return {'response':'Análise pronta.'}
  with patch('localai.request',side_effect=request):self.assertEqual(localai.generate('Analyze'),('model:local','Análise pronta.'))
 def test_crm_analysis_keeps_evidence(self):
  crm.import_csv(b'title,place_id\nCompany,abc\n','j');pid=crm.list_all()[0]['id'];crm.audit(pid)
  with patch('localai.generate',return_value=('model:local','Texto revisável.')):
   item=crm.analyze_ai(pid);self.assertTrue(item['audit']['findings']);self.assertEqual(item['audit']['ai'],'Texto revisável.')
 def test_ui_no_raw_block_or_photo_json(self):
  root=Path(__file__).resolve().parents[1];html=(root/'crm.html').read_text();js=(root/'static/crm.js').read_text()
  self.assertNotIn('id="raw"',html);self.assertIn('photo-gallery',html);self.assertNotIn("$('raw')",js);self.assertNotIn("['Fotos: dados coletados',d.images",js)
  uuid='12345678-1234-1234-1234-123456789abc';fragment=f'<tr><td>{uuid}</td><td>Busca</td></tr>'.encode()
  self.assertNotIn(uuid,gateway.transform_html(fragment).decode())
if __name__=='__main__':unittest.main()
