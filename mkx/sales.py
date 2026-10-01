"""Editable service catalog and versioned proposals. No external sending."""
import json
import uuid
from decimal import Decimal, InvalidOperation
from html import escape
import crm

DEFAULTS = [
 ('site', 'Site institucional', 'Apresentar a empresa e facilitar contato.', 'Páginas e conteúdo definidos na proposta; layout responsivo; publicação após aprovação.', 'Domínio, hospedagem, textos, imagens e manutenção definidos separadamente.'),
 ('conversion', 'Página de conversão', 'Organizar uma oferta e seus caminhos de contato.', 'Uma página; chamadas para ação; formulário ou link de contato conforme escopo.', 'Oferta, identidade visual e materiais fornecidos pelo cliente; tráfego pago não incluído.'),
 ('profile', 'Perfil da Empresa no Google', 'Revisar informações e apresentação do perfil.', 'Auditoria e ajustes permitidos com acesso autorizado; plano de melhorias.', 'Acesso do responsável necessário; sem garantia de posição ou aprovação pelo Google.'),
 ('content', 'Conteúdo e redes sociais', 'Planejar comunicação consistente.', 'Calendário, formatos e quantidade de peças definidos por período.', 'Aprovação do cliente; produção de fotos/vídeos, postagem e atendimento definidos à parte.'),
 ('ads', 'Gestão de tráfego', 'Planejar e acompanhar campanhas.', 'Planejamento, configuração e relatórios em canais acordados.', 'Verba de mídia separada; acessos autorizados; sem garantia de vendas.'),
 ('automation', 'Automação e IA', 'Reduzir tarefas repetitivas com um fluxo definido.', 'Mapeamento, implementação e orientação dentro do escopo aprovado.', 'APIs, ferramentas, limites de uso e suporte definidos separadamente.')]


def connect():
    db=crm.connect()
    db.executescript('''CREATE TABLE IF NOT EXISTS services(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, company TEXT NOT NULL, revision INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS proposal_versions(id TEXT, revision INTEGER, payload TEXT NOT NULL, PRIMARY KEY(id,revision));''')
    for pid,name,goal,scope,conditions in DEFAULTS:
        db.execute('INSERT OR IGNORE INTO services VALUES(?,?)',(pid,json.dumps({'id':pid,'name':name,'goal':goal,'scope':scope,'conditions':conditions,'price':'0.00','billing':'Único','days':15,'active':True})))
    db.commit()
    return db


def money(value):
    try:
        amount=Decimal(str(value).replace(',','.'))
        if not amount.is_finite() or amount<0 or amount>10000000 or amount.as_tuple().exponent < -2:
            raise ValueError('Valor deve estar entre 0 e 10 milhões, com até duas casas decimais.')
        return int(amount*100)
    except (InvalidOperation, TypeError):
        raise ValueError('Preço inválido. Use 2500.00 ou 2500,00.')


def text(body,key,limit=10000):
    value=str(body.get(key,'')).strip()
    if len(value)>limit:raise ValueError('Texto excede limite: '+key)
    return value


def catalog():
    with connect() as db:return [json.loads(r[0]) for r in db.execute('SELECT payload FROM services ORDER BY id')]


def save_service(body):
    pid=body.get('id') or uuid.uuid4().hex
    if not isinstance(pid,str) or len(pid)>64 or not pid.replace('-','').replace('_','').isalnum():raise ValueError('Serviço inválido.')
    price=money(body.get('price','0'))
    billing=body.get('billing','Único')
    if billing not in ('Único','Mensal'):raise ValueError('Tipo de cobrança inválido.')
    try:days=int(body.get('days',15))
    except (ValueError,TypeError):raise ValueError('Prazo inválido.')
    if not 1<=days<=365:raise ValueError('Prazo deve estar entre 1 e 365 dias.')
    item={'id':pid,'name':text(body,'name',160),'goal':text(body,'goal'),'scope':text(body,'scope'),'conditions':text(body,'conditions'),'price':f'{price/100:.2f}','billing':billing,'days':days,'active':bool(body.get('active',True))}
    if not item['name'] or not item['scope']:raise ValueError('Informe nome e escopo do serviço.')
    with connect() as db:db.execute('INSERT INTO services VALUES(?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',(pid,json.dumps(item)))
    return item


def proposal(pid, revision=None):
    with connect() as db:
        if revision is None:
            row=db.execute('SELECT v.payload FROM proposal_versions v JOIN proposals p ON p.id=v.id AND p.revision=v.revision WHERE p.id=?',(pid,)).fetchone()
        else:
            row=db.execute('SELECT payload FROM proposal_versions WHERE id=? AND revision=?',(pid,revision)).fetchone()
        if not row:raise ValueError('Proposta não encontrada.')
        item=json.loads(row[0])
        item['history']=[{'revision':r[0],**{k:v for k,v in json.loads(r[1]).items() if k in ('at','status')}} for r in db.execute('SELECT revision,payload FROM proposal_versions WHERE id=? ORDER BY revision DESC',(pid,))]
        return item


def proposals():
    with connect() as db:return [json.loads(r[0]) for r in db.execute('SELECT v.payload FROM proposal_versions v JOIN proposals p ON p.id=v.id AND p.revision=v.revision ORDER BY v.rowid DESC')]


def save_proposal(body):
    company=crm.get(str(body.get('company','')))
    if company['blocked']:raise ValueError('Empresa bloqueada para contato; proposta não pode ser criada ou alterada.')
    status=body.get('status','Rascunho')
    if status not in ('Rascunho','Pronta','Enviada manualmente','Aceita registrada','Recusada registrada'):raise ValueError('Status inválido.')
    lines=body.get('lines',[])
    if not isinstance(lines,list) or not 1<=len(lines)<=20:raise ValueError('Selecione de 1 a 20 itens.')
    clean=[]
    for line in lines:
        price=money(line.get('price','0'))
        billing=line.get('billing','Único')
        if billing not in ('Único','Mensal'):raise ValueError('Cobrança inválida.')
        name,scope=text(line,'name',160),text(line,'scope')
        if not name or not scope:raise ValueError('Cada item precisa de nome e escopo.')
        if status!='Rascunho' and price==0:raise ValueError('Defina preços antes de marcar a proposta como pronta.')
        clean.append({'name':name,'scope':scope,'conditions':text(line,'conditions'),'price_cents':price,'billing':billing})
    terms=text(body,'terms');evidence=text(body,'evidence');deadline=text(body,'deadline',500)
    if status!='Rascunho' and (not terms or not deadline or len(evidence)<20):raise ValueError('Defina contexto da oportunidade (20 caracteres), prazo e condições antes de concluir a proposta.')
    if status!='Rascunho' and company['intelligence']['review_state']!='Atualizada':raise ValueError('Atualize a revisão das evidências antes de concluir a proposta.')
    pid=body.get('id') or uuid.uuid4().hex
    if not isinstance(pid,str) or len(pid)!=32 or any(c not in '0123456789abcdef' for c in pid):raise ValueError('ID de proposta inválido.')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT revision,company FROM proposals WHERE id=?',(pid,)).fetchone()
        revision=existing['revision'] if existing else 0
        if existing and existing['company']!=company['id']:raise ValueError('Não é permitido mudar a empresa de uma proposta.')
        if body.get('revision',0)!=revision:raise ValueError('Proposta foi atualizada em outra aba. Reabra antes de salvar.')
        item={'id':pid,'revision':revision+1,'company':company['id'],'customer':{'name':company['data'].get('title',''),'address':company['data'].get('address','')},'status':status,'at':crm.now(),'lines':clean,'terms':terms,'evidence':evidence,'deadline':deadline,'review_snapshot':company['intelligence']['review'],'review_state':company['intelligence']['review_state'],'one_time_cents':sum(x['price_cents'] for x in clean if x['billing']=='Único'),'monthly_cents':sum(x['price_cents'] for x in clean if x['billing']=='Mensal')}
        db.execute('INSERT INTO proposal_versions VALUES(?,?,?)',(pid,item['revision'],json.dumps(item)))
        db.execute('INSERT INTO proposals VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision',(pid,company['id'],item['revision']))
        db.execute('INSERT INTO events VALUES(?,?,?)',(company['id'],crm.now(),'Proposta salva: '+pid[:8]+' · revisão '+str(item['revision'])+' · '+status))
    return proposal(pid)


def brl(cents):
    return 'R$ '+f'{cents/100:,.2f}'.replace(',','X').replace('.',',').replace('X','.')


def render(pid, revision=None):
    item=proposal(pid, revision)
    e=lambda v:escape(str(v))
    cards=''.join(f'<section><h3>{e(line["name"])} · {e(brl(line["price_cents"]))} {"/ mês" if line["billing"]=="Mensal" else ""}</h3><p>{e(line["scope"])}</p><small>{e(line["conditions"])}</small></section>' for line in item['lines'])
    warning='RASCUNHO — revise preços, escopo e evidências antes de apresentar.' if item['status']=='Rascunho' else 'Proposta comercial revisável. Status registrado internamente; não comprova envio ou aceite.'
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Proposta MKX — {e(item['customer']['name'])}</title><style>body{{font:16px Arial;color:#182d3e;max-width:900px;margin:45px auto;padding:20px}}h1{{font-size:36px}}section{{border-top:1px solid #ccd8e0;padding:18px 0;break-inside:avoid}}p{{white-space:pre-wrap;line-height:1.6}}small{{white-space:pre-wrap}}.badge{{background:#e6f7f0;padding:14px}}button{{padding:12px;background:#163b4f;color:white;border:0;cursor:pointer}}@media print{{button{{display:none}}body{{margin:0;max-width:none}}}}@page{{margin:18mm}}</style></head><body><button onclick="window.print()">Imprimir / salvar em PDF</button><p>MKX SOLUÇÕES · mkxsolucoes.com</p><h1>Proposta comercial</h1><h2>{e(item['customer']['name'])}</h2><p>{e(item['customer']['address'])}</p><small>{e(item['id'][:8])} · revisão {item['revision']} · {e(item['at'])}</small><p class="badge">{e(warning)}</p><h2>Contexto e oportunidade</h2><p>{e(item['evidence'])}</p>{cards}<section><h2>Investimento</h2><p>Serviços únicos: <strong>{e(brl(item['one_time_cents']))}</strong><br>Serviços mensais: <strong>{e(brl(item['monthly_cents']))} / mês</strong></p></section><section><h2>Prazo</h2><p>{e(item['deadline'])}</p><h2>Condições</h2><p>{e(item['terms'])}</p></section><p>Desenvolvido por MKX Soluções · <a href="https://mkxsolucoes.com">mkxsolucoes.com</a></p></body></html>'''.encode()
