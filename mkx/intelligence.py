"""Explainable commercial triage; scores are workflow heuristics, not predictions."""
import hashlib
import json

FIELDS = {'site_gap': 'Site não localizado após revisão',
          'conversion_gap': 'Melhoria de conversão identificada',
          'profile_gap': 'Melhoria do Perfil da Empresa identificada',
          'contact_fit': 'Canal comercial adequado revisado'}
VALUES = ('Pendente', 'Confirmado', 'Descartado')


def fingerprint(item):
    site = dict(item.get('audit', {}).get('site', {}))
    site.pop('at', None)
    return hashlib.sha256(json.dumps({'data': item['data'], 'site': site}, sort_keys=True).encode()).hexdigest()


def summarize(item, review):
    fresh = bool(review) and review.get('fingerprint') == fingerprint(item)
    answers = review.get('answers', {}) if fresh else {}
    confirmed = [k for k in FIELDS if answers.get(k) == 'Confirmado']
    opportunities = [k for k in confirmed if k != 'contact_fit']
    blocked = bool(item.get('blocked'))
    score = 0
    reasons = []
    services = []
    for key, points, service in [('site_gap', 35, 'Site institucional'), ('conversion_gap', 25, 'Página de conversão / revisão do site'), ('profile_gap', 20, 'Gestão do Perfil da Empresa')]:
        if key in confirmed:
            score += points
            reasons.append({'label': FIELDS[key], 'points': points, 'evidence': review.get('evidence', '')})
            services.append(service)
    if 'contact_fit' in confirmed:
        score += 20
        reasons.append({'label': FIELDS['contact_fit'], 'points': 20, 'evidence': review.get('evidence', '')})
    score = min(100, score)
    if blocked:
        score, priority, next_action = 0, 'Não contatar', 'Respeitar bloqueio de contato.'
        reasons, services = [], []
    elif not fresh:
        priority = 'Revisão pendente'
        next_action = 'Atualizar revisão humana.' if review else 'Verificar o site e revisar evidências.'
    elif opportunities and 'contact_fit' in confirmed:
        priority, next_action = 'Prioritária', 'Preparar abordagem sobre a oportunidade confirmada; revisar destinatário antes do contato.'
    elif opportunities:
        priority, next_action = 'Qualificar contato', 'Revisar um canal comercial adequado antes de preparar abordagem.'
    else:
        priority, next_action = 'Sem oportunidade confirmada', 'Investigar outra necessidade ou descartar a hipótese atual.'
    site = item.get('audit', {}).get('site', {})
    return {'score': score, 'priority': priority, 'reasons': reasons, 'services': services,
            'next_action': next_action, 'review_state': 'Atualizada' if fresh else ('Desatualizada' if review else 'Pendente'),
            'review': review, 'site_state': site.get('state', 'Não analisado'),
            'contact_available': bool(item['data'].get('phone') or item['data'].get('emails') or item['data'].get('email') or site.get('emails') or site.get('phones') or site.get('whatsapp')),
            'notice': 'Pontuação de triagem baseada em revisão humana. Não estima probabilidade de compra, receita ou qualidade da empresa.'}
