"""Commercial snapshot and manually confirmed cash ledger; no bank integration."""
import csv
import io
import json
import uuid
from datetime import datetime, date, timedelta, timezone
import crm
import sales
import relationship

FORTALEZA = timezone(timedelta(hours=-3))


def connect():
    db=crm.connect()
    db.executescript('''CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY,company TEXT NOT NULL,proposal TEXT NOT NULL,kind TEXT NOT NULL,amount INTEGER NOT NULL,day TEXT NOT NULL,reference TEXT NOT NULL,notes TEXT NOT NULL,at TEXT NOT NULL,voided INTEGER NOT NULL DEFAULT 0,void_reason TEXT NOT NULL DEFAULT '');
    CREATE UNIQUE INDEX IF NOT EXISTS receipt_reference ON receipts(company,kind,reference) WHERE voided=0;''')
    return db


def day_value(value):
    try:return date.fromisoformat(str(value)).isoformat()
    except ValueError:raise ValueError('Data deve estar em AAAA-MM-DD.')


def receipts():
    with connect() as db:
        rows=db.execute('SELECT r.*,p.data FROM receipts r JOIN prospects p ON r.company=p.id ORDER BY r.day DESC,r.at DESC').fetchall()
        out=[]
        for row in rows:
            item=dict(row);item['company_name']=json.loads(item.pop('data')).get('title','');out.append(item)
        return out


def save_receipt(body):
    company=crm.get(str(body.get('company','')))
    if body.get('confirmed') is not True:raise ValueError('Confirme que conferiu o movimento antes de registrar.')
    amount=sales.money(body.get('amount','0'))
    if amount<=0:raise ValueError('Valor precisa ser maior que zero.')
    kind=body.get('kind','Recebimento')
    if kind not in ('Recebimento','Estorno'):raise ValueError('Tipo inválido.')
    day=day_value(body.get('day',''))
    if date.fromisoformat(day)>datetime.now(FORTALEZA).date():raise ValueError('Recebimento/estorno não pode ter data futura.')
    reference=str(body.get('reference','')).strip();notes=str(body.get('notes','')).strip()
    if not reference or len(reference)>200 or len(notes)>10000:raise ValueError('Informe referência de até 200 caracteres e notas de até 10 mil.')
    proposal=str(body.get('proposal','')).strip()
    if proposal and sales.proposal(proposal)['company']!=company['id']:raise ValueError('Proposta pertence a outra empresa.')
    pid=body.get('id')
    if not isinstance(pid,str) or len(pid)!=32 or any(c not in '0123456789abcdef' for c in pid):raise ValueError('ID do movimento inválido.')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT * FROM receipts WHERE id=?',(pid,)).fetchone()
        fields=(company['id'],proposal,kind,amount,day,reference,notes)
        if existing:
            if tuple(existing[k] for k in ('company','proposal','kind','amount','day','reference','notes'))!=fields:raise ValueError('ID já usado com outros dados.')
            return dict(existing)
        if db.execute('SELECT id FROM receipts WHERE company=? AND kind=? AND reference=? AND voided=0',(company['id'],kind,reference)).fetchone():raise ValueError('Já existe movimento com essa referência para a empresa e tipo.')
        db.execute('INSERT INTO receipts(id,company,proposal,kind,amount,day,reference,notes,at) VALUES(?,?,?,?,?,?,?,?,?)',(pid,*fields,crm.now()))
        db.execute('INSERT INTO events VALUES(?,?,?)',(company['id'],crm.now(),kind+' registrado manualmente: '+sales.brl(amount)+' · '+reference))
    return next(r for r in receipts() if r['id']==pid)


def void_receipt(pid,reason):
    reason=str(reason).strip()
    if len(reason)<10 or len(reason)>1000:raise ValueError('Explique a correção com 10 a 1000 caracteres.')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM receipts WHERE id=?',(pid,)).fetchone()
        if not row:raise ValueError('Movimento não encontrado.')
        if not row['voided']:
            db.execute('UPDATE receipts SET voided=1,void_reason=? WHERE id=?',(reason,pid))
            db.execute('INSERT INTO events VALUES(?,?,?)',(row['company'],crm.now(),'Movimento anulado por correção: '+pid[:8]+' · '+reason))
    return {'id':pid,'voided':True}


def snapshot(start=None,end=None):
    end=day_value(end) if end else datetime.now(FORTALEZA).date().isoformat()
    start=day_value(start) if start else (date.fromisoformat(end)-timedelta(days=29)).isoformat()
    if start>end:raise ValueError('Data inicial deve ser anterior ou igual à final.')
    def in_period(stamp):return start<=datetime.fromisoformat(stamp).astimezone(FORTALEZA).date().isoformat()<=end
    companies=crm.list_all();proposals=sales.proposals();payments=receipts()
    with crm.connect() as db:events=[dict(r) for r in db.execute('SELECT * FROM interactions ORDER BY at DESC')]
    activity=[r for r in events if in_period(r['at'])]
    contacts={r['company'] for r in activity if r['kind']=='Contato realizado'}
    responses={r['company'] for r in activity if r['kind']=='Resposta recebida'}
    meetings={r['company'] for r in activity if r['kind']=='Reunião realizada'}
    accepted=[p for p in proposals if p['status']=='Aceita registrada']
    offered=[p for p in proposals if p['status'] in ('Pronta','Enviada manualmente')]
    period_proposals=[p for p in proposals if in_period(p['at'])]
    period_payments=[r for r in payments if start<=r['day']<=end]
    valid=[r for r in period_payments if not r['voided']]
    gross=sum(r['amount'] for r in valid if r['kind']=='Recebimento');refunds=sum(r['amount'] for r in valid if r['kind']=='Estorno')
    timeline={}
    for r in valid:
        timeline[r['day']]=timeline.get(r['day'],0)+r['amount']*(1 if r['kind']=='Recebimento' else -1)
    return {'period':{'start':start,'end':end,'timezone':'America/Fortaleza'},
            'portfolio':{'companies':len(companies),'qualified':sum(p['intelligence']['priority']=='Prioritária' for p in companies),'won':sum(p['stage']=='Ganha' for p in companies),'blocked':sum(bool(p['blocked']) for p in companies),'stages':{s:sum(p['stage']==s for p in companies) for s in crm.STAGES}},
            'activity':{'contacted_companies':len(contacts),'responding_companies':len(responses),'meeting_companies':len(meetings),'records':len(activity),'proposals_updated':len(period_proposals)},
            'proposals':{'total':len(proposals),'accepted':len(accepted),'offered':len(offered),'accepted_one_time':sum(p['one_time_cents'] for p in accepted),'accepted_monthly':sum(p['monthly_cents'] for p in accepted),'offered_one_time':sum(p['one_time_cents'] for p in offered),'offered_monthly':sum(p['monthly_cents'] for p in offered)},
            'cash':{'gross':gross,'refunds':refunds,'net':gross-refunds,'records':len(valid),'timeline':[{'day':day,'net':net} for day,net in sorted(timeline.items())]},
            'receipts':period_payments,'next_actions':[t for t in relationship.tasks() if t['status']=='Pendente'][:12],
            'notice':'Carteira e propostas representam o estado atual. Atividade usa a data do registro; caixa usa a data informada do movimento. Não é conciliação bancária, lucro ou previsão de vendas.'}


def export(start=None,end=None):
    data=snapshot(start,end);out=io.StringIO();writer=csv.writer(out)
    writer.writerow(['Empresa','Tipo','Data','Valor R$','Referência','Anulado','Motivo','Notas'])
    for r in data['receipts']:
        values=[r['company_name'],r['kind'],r['day'],f"{r['amount']/100:.2f}",r['reference'],str(bool(r['voided'])),r['void_reason'],r['notes']]
        writer.writerow(["'"+v if v.lstrip().startswith(('=','+','-','@')) else v for v in values])
    return ('\ufeff'+out.getvalue()).encode()
