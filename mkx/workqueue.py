"""Durable local import/verification queue, one worker, no outbound messages."""
import hashlib
import http.client
import json
import re
import threading
import time
import uuid
import crm

STOP = threading.Event()
ENGINE_PORT = 8090
DEFAULTS = {'paused':False,'auto_import':True,'auto_verify':False}


def connect():
    db=crm.connect()
    db.executescript('''CREATE TABLE IF NOT EXISTS queue_config(id INTEGER PRIMARY KEY,payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS queue_items(id TEXT PRIMARY KEY, unique_key TEXT UNIQUE, kind TEXT NOT NULL,target TEXT NOT NULL,state TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,created TEXT NOT NULL,updated TEXT NOT NULL,error TEXT NOT NULL DEFAULT '',result TEXT NOT NULL DEFAULT '{}');''')
    db.execute('INSERT OR IGNORE INTO queue_config VALUES(1,?)',(json.dumps({**DEFAULTS,'last_scan':'','scan_error':''}),));db.commit()
    return db


def config():
    with connect() as db:return json.loads(db.execute('SELECT payload FROM queue_config WHERE id=1').fetchone()[0])


def settings(body):
    if any(k not in DEFAULTS or type(v) is not bool for k,v in body.items()):raise ValueError('Configuração inválida.')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE');cfg=json.loads(db.execute('SELECT payload FROM queue_config WHERE id=1').fetchone()[0]);cfg.update(body)
        db.execute('UPDATE queue_config SET payload=? WHERE id=1',(json.dumps(cfg),))
    return cfg


def enqueue(kind,target,key=None):
    if kind not in ('import','verify'):raise ValueError('Tipo de tarefa inválido.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',target):raise ValueError('Destino inválido.')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute("SELECT id FROM queue_items WHERE kind=? AND target=? AND state IN ('Pendente','Executando')",(kind,target)).fetchone()
        if existing:return existing[0]
        if key:
            existing=db.execute('SELECT id FROM queue_items WHERE unique_key=?',(key,)).fetchone()
            if existing:return existing[0]
        pid=uuid.uuid4().hex;stamp=crm.now()
        db.execute('INSERT INTO queue_items(id,unique_key,kind,target,state,created,updated) VALUES(?,?,?,?,?,?,?)',(pid,key or pid,kind,target,'Pendente',stamp,stamp))
    return pid


def enqueue_companies(ids,automatic=False):
    if not isinstance(ids,list) or len(ids)>1000:raise ValueError('Selecione até 1000 empresas por lote.')
    queued=skipped=0
    for pid in set(ids):
        item=crm.get(pid)
        if item['blocked'] or not item['data'].get('website','').strip():skipped+=1;continue
        key=None
        if automatic:key='verify:'+pid+':'+hashlib.sha256(json.dumps(item['data'],sort_keys=True).encode()).hexdigest()
        enqueue('verify',pid,key);queued+=1
    return {'eligible':queued,'skipped':skipped}


def engine_get(path,limit=10_000_000):
    conn=http.client.HTTPConnection('127.0.0.1',ENGINE_PORT,timeout=8)
    try:
        conn.request('GET',path);resp=conn.getresponse();data=resp.read(limit+1)
        if resp.status!=200:raise ValueError('Motor retornou HTTP '+str(resp.status))
        if len(data)>limit:raise ValueError('Resposta excede limite de tamanho.')
        return data
    finally:conn.close()


def scan(fetch=engine_get):
    cfg=config()
    if cfg['paused'] or not cfg['auto_import']:return
    error=''
    try:
        jobs=json.loads(fetch('/api/v1/jobs',2_000_000)) or []
        if not isinstance(jobs,list):raise ValueError('Formato inesperado da lista de buscas do motor.')
        for job in jobs:
            if not isinstance(job,dict):continue
            pid=str(job.get('ID',job.get('id','')));status=job.get('Status',job.get('status',''))
            if status=='ok' and re.fullmatch(r'[A-Za-z0-9_-]{1,100}',pid):enqueue('import',pid,'import:'+pid)
    except (ValueError,OSError,http.client.HTTPException) as exc:error=str(exc)[:500]
    with connect() as db:
        db.execute('BEGIN IMMEDIATE');current=json.loads(db.execute('SELECT payload FROM queue_config WHERE id=1').fetchone()[0]);current.update(last_scan=crm.now(),scan_error=error)
        db.execute('UPDATE queue_config SET payload=? WHERE id=1',(json.dumps(current),))


def recover():
    with connect() as db:
        db.execute("UPDATE queue_items SET state=CASE WHEN attempts>=3 THEN 'Falhou' ELSE 'Pendente' END,error='Execução interrompida; recuperada na inicialização.',updated=? WHERE state='Executando'",(crm.now(),))


def claim():
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        cfg=json.loads(db.execute('SELECT payload FROM queue_config WHERE id=1').fetchone()[0])
        if cfg['paused']:return None
        row=db.execute("SELECT * FROM queue_items WHERE state='Pendente' ORDER BY created,id LIMIT 1").fetchone()
        if not row:return None
        db.execute("UPDATE queue_items SET state='Executando',attempts=attempts+1,updated=? WHERE id=?",(crm.now(),row['id']))
        item=dict(row);item['attempts']+=1;return item


def process_one(fetch=engine_get):
    item=claim()
    if not item:return False
    state='Concluída';error='';result={}
    try:
        if item['kind']=='import':
            result=crm.import_csv(fetch('/download?id='+item['target']),item['target'])
            if config()['auto_verify']:
                ids=[p['id'] for p in crm.list_all() if item['target'] in p['sources']]
                result['verification']={'eligible':0,'skipped':0}
                for offset in range(0,len(ids),1000):
                    batch=enqueue_companies(ids[offset:offset+1000],True)
                    for key in batch:result['verification'][key]+=batch[key]
        else:
            company=crm.get(item['target'])
            if company['blocked']:
                state='Cancelada';result={'message':'Empresa bloqueada para contato.'}
            else:
                verified=crm.verify_site(item['target']);site=verified['audit']['site']
                result={'site_state':site['state'],'message':site['message']}
                if site['state']=='Erro':state='Falhou';error=site['message']
    except Exception as exc:
        state='Falhou';error=str(exc)[:800]
    with connect() as db:
        db.execute('UPDATE queue_items SET state=?,error=?,result=?,updated=? WHERE id=?',(state,error,json.dumps(result),crm.now(),item['id']))
    return True


def action(pid,command):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM queue_items WHERE id=?',(pid,)).fetchone()
        if not row:raise ValueError('Tarefa não encontrada.')
        if command=='retry':
            if row['state'] not in ('Falhou','Cancelada') or row['attempts']>=3:raise ValueError('Repetição disponível para falhas/cancelamentos com menos de 3 tentativas.')
            active=db.execute("SELECT id FROM queue_items WHERE kind=? AND target=? AND state IN ('Pendente','Executando')",(row['kind'],row['target'])).fetchone()
            if active:raise ValueError('Já existe tarefa ativa para esse destino.')
            state='Pendente'
        elif command=='cancel' and row['state']=='Pendente':state='Cancelada'
        else:raise ValueError('Só é possível cancelar uma tarefa pendente. Aguarde a tarefa em execução.')
        db.execute('UPDATE queue_items SET state=?,updated=? WHERE id=?',(state,crm.now(),pid))
    return snapshot()


def snapshot():
    with connect() as db:
        counts={r[0]:r[1] for r in db.execute('SELECT state,count(*) FROM queue_items GROUP BY state')}
        rows=db.execute('SELECT * FROM queue_items ORDER BY created DESC,id LIMIT 300').fetchall()
        items=[]
        for row in rows:
            item=dict(row);item['result']=json.loads(item['result']);items.append(item)
    total=sum(counts.values());treated=sum(counts.get(k,0) for k in ('Concluída','Falhou','Cancelada'))
    return {'config':config(),'counts':counts,'total':total,'treated':treated,'percent':round(100*treated/total) if total else 0,'items':items,'worker':'Um processo por vez; importações e verificações locais.'}


def worker():
    recover();last_scan=0
    while not STOP.is_set():
        try:
            if time.monotonic()-last_scan>=15:scan();last_scan=time.monotonic()
            if not process_one():STOP.wait(2)
        except Exception as exc:
            print('MKX fila: '+str(exc),flush=True);STOP.wait(3)


def start(port=8090):
    global ENGINE_PORT
    ENGINE_PORT=port;STOP.clear();thread=threading.Thread(target=worker,daemon=True);thread.start();return thread
