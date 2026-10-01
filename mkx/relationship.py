"""Local follow-ups and manual interaction history. Does not send messages."""
import uuid
from datetime import datetime, timezone
import crm

KINDS = ['Contato realizado', 'Resposta recebida', 'Reunião realizada', 'Proposta apresentada', 'Sem resposta', 'Recusa / descadastro', 'Nota interna']
CHANNELS = ['E-mail', 'WhatsApp', 'Telefone', 'Reunião', 'Outro']

def due_value(value):
    try:
        date=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        if date.tzinfo is None:raise ValueError()
        return date.astimezone(timezone.utc).isoformat()
    except (ValueError,TypeError,OverflowError):raise ValueError('Informe data e hora com fuso horário.')


def tasks():
    with crm.connect() as db:
        rows=db.execute('SELECT t.*,p.data,p.blocked FROM tasks t JOIN prospects p ON t.company=p.id ORDER BY t.due,t.id').fetchall()
        import json
        result=[]
        for row in rows:
            item=dict(row);item['company_name']=json.loads(item.pop('data')).get('title','')
            item['overdue']=item['status']=='Pendente' and datetime.fromisoformat(item['due'])<datetime.now(timezone.utc)
            result.append(item)
        return result


def save_task(body):
    company=crm.get(str(body.get('company','')))
    title=str(body.get('title','')).strip();notes=str(body.get('notes','')).strip()
    if not title or len(title)>200 or len(notes)>10000:raise ValueError('Título obrigatório (até 200 caracteres) e notas de até 10 mil caracteres.')
    due=due_value(body.get('due',''))
    status=body.get('status','Pendente')
    if status not in ('Pendente','Concluída','Cancelada'):raise ValueError('Status de tarefa inválido.')
    pid=body.get('id') or uuid.uuid4().hex
    if not isinstance(pid,str) or len(pid)!=32 or any(c not in '0123456789abcdef' for c in pid):raise ValueError('Tarefa inválida.')
    with crm.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        blocked=db.execute('SELECT blocked FROM prospects WHERE id=?',(company['id'],)).fetchone()[0]
        if blocked:raise ValueError('Empresa bloqueada para contato; tarefas não podem ser criadas ou alteradas.')
        existing=db.execute('SELECT revision,company FROM tasks WHERE id=?',(pid,)).fetchone()
        revision=existing['revision'] if existing else 0
        if existing and existing['company']!=company['id']:raise ValueError('Não é permitido trocar a empresa da tarefa.')
        if body.get('revision',0)!=revision:raise ValueError('Tarefa mudou em outra aba. Atualize antes de salvar.')
        db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,due=excluded.due,notes=excluded.notes,status=excluded.status,revision=excluded.revision,updated=excluded.updated',(pid,company['id'],title,due,notes,status,revision+1,crm.now()))
        db.execute('INSERT INTO events VALUES(?,?,?)',(company['id'],crm.now(),'Próxima ação: '+title+' · '+status))
    return next(item for item in tasks() if item['id']==pid)


def interactions(company=None):
    with crm.connect() as db:
        if company:
            crm.get(company)
            rows=db.execute('SELECT * FROM interactions WHERE company=? ORDER BY at DESC LIMIT 500',(company,))
        else:
            rows=db.execute('SELECT * FROM interactions ORDER BY at DESC LIMIT 500')
        return [dict(r) for r in rows]


def log_interaction(body):
    company=crm.get(str(body.get('company','')))
    kind=body.get('kind','Nota interna');channel=body.get('channel','Outro')
    notes=str(body.get('notes','')).strip()
    if kind not in KINDS or channel not in CHANNELS:raise ValueError('Tipo ou canal inválido.')
    if not notes or len(notes)>10000:raise ValueError('Descreva o contato ou resposta (até 10 mil caracteres).')
    # Client-generated stable IDs prevent duplicate records on retry.
    pid=body.get('id')
    if not isinstance(pid,str) or len(pid)!=32 or any(c not in '0123456789abcdef' for c in pid):raise ValueError('Identificador de registro inválido.')
    at=crm.now()
    with crm.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT * FROM interactions WHERE id=?',(pid,)).fetchone()
        if existing:
            if (existing['company'],existing['kind'],existing['channel'],existing['notes'])!=(company['id'],kind,channel,notes):raise ValueError('ID já utilizado em outro registro.')
            return dict(existing)
        if kind=='Recusa / descadastro':
            db.execute("UPDATE prospects SET blocked=1,stage='Não contatar',updated=? WHERE id=?",(at,company['id']))
            db.execute("UPDATE tasks SET status='Cancelada',revision=revision+1,updated=? WHERE company=? AND status='Pendente'",(at,company['id']))
        db.execute('INSERT INTO interactions VALUES(?,?,?,?,?,?)',(pid,company['id'],kind,channel,notes,at))
        db.execute('INSERT INTO events VALUES(?,?,?)',(company['id'],at,kind+' · '+channel+' · '+notes[:500]))
    return {'id':pid,'company':company['id'],'kind':kind,'channel':channel,'notes':notes,'at':at}


def draft(company,channel):
    item=crm.get(company)
    if item['blocked']:raise ValueError('Empresa bloqueada para contato.')
    if channel not in ('E-mail','WhatsApp'):raise ValueError('Selecione E-mail ou WhatsApp.')
    intel=item['intelligence']
    if intel['review_state']!='Atualizada' or intel['priority']!='Prioritária':raise ValueError('Confirme uma oportunidade e um canal comercial adequado na revisão antes de personalizar a abordagem.')
    service=intel['services'][0]
    name=item['data'].get('title','sua empresa')
    body=(f'Olá, equipe da {name}. Sou da MKX Soluções.\n\n'
          f'Após revisar a presença digital de vocês, identificamos uma possibilidade de melhoria relacionada a {service.lower()}. '
          'Gostaria de saber se esse tema é uma prioridade para vocês e se podemos compartilhar uma sugestão breve.\n\n'
          'MKX Soluções\nhttps://mkxsolucoes.com\n\nSe preferirem não receber novos contatos, basta informar. Registraremos sua preferência.')
    return {'subject':'MKX Soluções — '+name,'body':body,'channel':channel,
            'warning':'Rascunho para revisão e envio manual. Adapte com uma observação concreta das fontes, assinatura pessoal e destinatário. Não afirma que já houve contato nem garante resultados.'}
