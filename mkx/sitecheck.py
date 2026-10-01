"""Bounded home-page checks, with DNS-pinned connections to public addresses."""
import http.client
import ipaddress
import socket
import ssl
import time
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit, urljoin, unquote

MAX_BYTES = 1_500_000
SOCIAL = ('instagram.com', 'facebook.com', 'linkedin.com', 'tiktok.com', 'youtube.com')


def target(url):
    p = urlsplit(url)
    if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password:
        raise ValueError('Endereço deve ser HTTP/HTTPS público, sem credenciais.')
    if p.port and p.port not in (80, 443):
        raise ValueError('Porta de destino não permitida.')
    host = p.hostname.encode('idna').decode('ascii')
    addresses = socket.getaddrinfo(host, p.port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    ips = {entry[4][0] for entry in addresses}
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise ValueError('Destino privado, reservado ou local bloqueado.')
    return p, host, sorted(ips)[0]


def fetch(url, timeout):
    p, host, ip = target(url)
    port = p.port or (443 if p.scheme == 'https' else 80)
    conn = http.client.HTTPConnection(host, port, timeout=timeout)
    def connect():
        sock = socket.create_connection((ip, port), timeout=timeout)
        if p.scheme == 'https':
            try:
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
            except Exception:
                sock.close()
                raise
        conn.sock = sock
    conn.connect = connect
    try:
        conn.request('GET', urlunsplit(('', '', p.path or '/', p.query, '')), headers={
            'Host': host + (':' + str(p.port) if p.port else ''),
            'User-Agent': 'MKX-Radar/0.4 (website-check; https://mkxsolucoes.com)',
            'Accept': 'text/html', 'Accept-Encoding': 'identity'})
        r = conn.getresponse()
        deadline = time.monotonic() + timeout
        chunks, size = [], 0
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError('Tempo limite para leitura da página.')
            chunk = r.read1(min(65536, MAX_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_BYTES:
                break
        data = b''.join(chunks)
        if len(data) > MAX_BYTES:
            raise ValueError('Página excede limite de 1,5 MB.')
        return r.status, dict((k.lower(), v) for k, v in r.getheaders()), data
    finally:
        conn.close()


class Page(HTMLParser):
    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.title = ''
        self.in_title = False
        self.description = ''
        self.viewport = False
        self.forms = 0
        self.socials = set()
        self.emails = set()
        self.phones = set()
        self.whatsapp = set()
        self.images = 0
        self.images_missing_alt = 0
        self.contact_links = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title': self.in_title = True
        if tag == 'meta':
            name = a.get('name', '').lower()
            if name == 'description': self.description = a.get('content', '')[:600]
            if name == 'viewport': self.viewport = bool(a.get('content'))
        if tag == 'form': self.forms += 1
        if tag == 'img':
            self.images += 1
            if not a.get('alt', '').strip(): self.images_missing_alt += 1
        if tag != 'a': return
        href = a.get('href', '').strip()
        if href.lower().startswith('mailto:'):
            value = unquote(href[7:].split('?')[0])
            if '@' in value: self.emails.add(value[:250])
            return
        if href.lower().startswith('tel:'):
            self.phones.add(unquote(href[4:])[:100]); return
        url = urljoin(self.url, href)
        p = urlsplit(url)
        if p.scheme not in ('http', 'https') or not p.hostname: return
        host = p.hostname.lower().removeprefix('www.')
        if any(host == s or host.endswith('.' + s) for s in SOCIAL):
            # Exclude sharing dialogs, which do not identify an official profile.
            if not any(word in (p.path + p.query).lower() for word in ('sharer', '/share', '/intent')):
                self.socials.add(url[:1000])
        if host in ('wa.me', 'api.whatsapp.com', 'web.whatsapp.com'):
            self.whatsapp.add(url[:1000])
        if p.hostname == urlsplit(self.url).hostname and any(word in p.path.lower() for word in ('contato', 'contact', 'agend')):
            self.contact_links.add(url[:1000])
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title = (self.title + data)[:500]


def check(url, transport=fetch):
    result = {'source': url, 'scope': 'Página inicial; sem execução de JavaScript', 'state': 'Não analisado'}
    if not url.strip():
        result.update(state='Não informado', message='Site não informado na coleta. Confirme manualmente.'); return result
    if '://' not in url: url = 'https://' + url
    deadline = time.monotonic() + 25
    redirects = []
    try:
        for _ in range(4):
            remaining = deadline - time.monotonic()
            if remaining <= 0: raise TimeoutError('Tempo limite de verificação.')
            status, headers, data = transport(url, min(8, remaining))
            if status in (301, 302, 303, 307, 308):
                location = headers.get('location')
                if not location: raise ValueError('Redirecionamento sem destino.')
                redirects.append({'url': url, 'status': status})
                url = urljoin(url, location)
                continue
            result.update(final_url=url, http_status=status, redirects=redirects, https=urlsplit(url).scheme == 'https')
            if status in (401,403,429):
                result.update(state='Bloqueado', message='Site restringiu a consulta. Revise no navegador.'); return result
            if status >= 400:
                result.update(state='Erro', message='Página retornou erro HTTP; isso não comprova ausência de site.'); return result
            if status != 200:
                result.update(state='Não conclusivo', message='Resposta diferente de 200.'); return result
            if 'text/html' not in headers.get('content-type', '').lower():
                result.update(state='Não conclusivo', message='Resposta não é HTML.'); return result
            charset = 'utf-8'
            import re
            match = re.search(r'charset=([\w-]+)', headers.get('content-type', ''))
            if match: charset = match.group(1)
            try: text = data.decode(charset, errors='replace')
            except LookupError: text = data.decode('utf-8', errors='replace')
            page = Page(url); page.feed(text)
            result.update(state='Verificado', title=page.title.strip(), description=page.description,
                viewport=page.viewport, forms=page.forms, images=page.images,
                images_missing_alt=page.images_missing_alt, socials=sorted(page.socials),
                emails=sorted(page.emails), phones=sorted(page.phones), whatsapp=sorted(page.whatsapp),
                contact_links=sorted(page.contact_links), message='Página acessível. Indicadores técnicos não equivalem a avaliação visual ou desempenho.')
            return result
        raise ValueError('Limite de redirecionamentos excedido.')
    except (ValueError, OSError, http.client.HTTPException) as exc:
        result.update(state='Erro', message=str(exc)[:400], final_url=url)
        return result
