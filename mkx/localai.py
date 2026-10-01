"""Local Ollama model selection persisted in the MKX database."""
import http.client
import json
import os
import crm


def selected():
    with crm.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS ai_settings(id INTEGER PRIMARY KEY,model TEXT NOT NULL)')
        row=db.execute('SELECT model FROM ai_settings WHERE id=1').fetchone()
    return row[0] if row else os.environ.get('MKX_OLLAMA_MODEL','').strip()


def request(path,body=None,timeout=8):
    conn=http.client.HTTPConnection('host.docker.internal',11434,timeout=timeout)
    try:
        conn.request('GET' if body is None else 'POST',path,None if body is None else json.dumps(body),{'Content-Type':'application/json'})
        response=conn.getresponse();raw=response.read(1_000_001)
        if response.status!=200 or len(raw)>1_000_000:raise ValueError('Ollama não concluiu a solicitação. Confira se o modelo está disponível.')
        return json.loads(raw)
    except (OSError,http.client.HTTPException,json.JSONDecodeError) as exc:
        raise ValueError('Não conseguimos conectar ao Ollama. Abra o aplicativo no Windows e confira a conexão com o Docker.') from exc
    finally:conn.close()


def status():
    model=selected()
    try:
        data=request('/api/tags');models=[]
        if not isinstance(data,dict) or not isinstance(data.get('models'),list):raise ValueError('Ollama retornou uma lista de modelos inválida. Tente atualizar a conexão.')
        for item in data.get('models',[]):
            name=item.get('name',item.get('model',''))
            if not isinstance(name,str) or not name:continue
            # Remote/cloud models are not offered as a local option.
            if 'cloud' in name.lower() or item.get('remote_host') or item.get('remote_model'):continue
            models.append({'name':name,'size':item.get('size',0),'family':item.get('details',{}).get('family','')})
        return {'connected':True,'selected':model,'models':models,'message':'Ollama conectado.' if models else 'Ollama conectado, mas nenhum modelo local foi encontrado.'}
    except ValueError as exc:return {'connected':False,'selected':model,'models':[],'message':str(exc)}


def save(model):
    if not isinstance(model,str) or len(model)>200:raise ValueError('Modelo inválido.')
    if model:
        data=status()
        if not data['connected']:raise ValueError(data['message'])
        if model not in [m['name'] for m in data['models']]:raise ValueError('Escolha um modelo local disponível na lista.')
    with crm.connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS ai_settings(id INTEGER PRIMARY KEY,model TEXT NOT NULL)')
        db.execute('INSERT INTO ai_settings VALUES(1,?) ON CONFLICT(id) DO UPDATE SET model=excluded.model',(model,))
    return {'selected':model,'message':'Modelo salvo.' if model else 'Análise por IA desativada. Diagnóstico por regras continua disponível.'}


def generate(prompt):
    model=selected()
    if not model:raise ValueError('Escolha seu modelo em IA local no menu lateral.')
    available=status()
    if model not in [m['name'] for m in available['models']]:raise ValueError(available['message'] if not available['connected'] else 'O modelo selecionado não está disponível. Confira IA local.')
    data=request('/api/generate',{'model':model,'prompt':prompt,'stream':False,'options':{'num_predict':700}},120)
    answer=data.get('response','')
    if not isinstance(answer,str) or not answer.strip():raise ValueError('O modelo retornou resposta vazia. Tente outro modelo.')
    return model,answer[:20000]


def test():
    model,answer=generate('Responda em português, somente: IA local pronta para analisar empresas.')
    return {'model':model,'answer':answer,'message':'Teste de geração concluído.'}
