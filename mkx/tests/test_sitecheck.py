import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import unittest
from unittest.mock import patch
import sitecheck

class WebsiteTests(unittest.TestCase):
    def test_html_evidence(self):
        page=b'''<title>Clinic</title><meta name="viewport" content="width=device-width"><meta name="description" content="Care"><a href="https://instagram.com/clinic">IG</a><a href="https://facebook.com/sharer.php?u=x">share</a><a href="https://wa.me/558899">WA</a><a href="mailto:contato@example.com">email</a><a href="tel:+558899">phone</a><form></form><img src="a"><a href="/contato">contact</a>'''
        r=sitecheck.check('https://example.com',lambda u,t:(200,{'content-type':'text/html'},page))
        self.assertEqual(r['state'],'Verificado')
        self.assertTrue(r['viewport'])
        self.assertEqual(r['forms'],1)
        self.assertEqual(len(r['socials']),1)
        self.assertEqual(r['emails'],['contato@example.com'])
        self.assertEqual(len(r['whatsapp']),1)
        self.assertEqual(r['contact_links'],['https://example.com/contato'])
    def test_absence_block_error_not_html(self):
        self.assertEqual(sitecheck.check('')['state'],'Não informado')
        for code,state in [(403,'Bloqueado'),(429,'Bloqueado'),(404,'Erro')]:
            self.assertEqual(sitecheck.check('https://example.com',lambda u,t:(code,{},b''))['state'],state)
        self.assertEqual(sitecheck.check('https://example.com',lambda u,t:(200,{'content-type':'image/png'},b''))['state'],'Não conclusivo')
    def test_redirect_followed_and_limited(self):
        calls=[]
        def transport(u,t):
            calls.append(u)
            return (302,{'location':'/final'},b'') if len(calls)==1 else (200,{'content-type':'text/html'},b'<title>Final</title>')
        result=sitecheck.check('https://example.com',transport)
        self.assertEqual(result['final_url'],'https://example.com/final')
        self.assertEqual(len(result['redirects']),1)
        self.assertEqual(sitecheck.check('https://example.com',lambda u,t:(302,{'location':'/loop'},b''))['state'],'Erro')
    def test_private_and_mixed_dns_are_blocked(self):
        for address in ('127.0.0.1','10.0.0.2','169.254.169.254','::1'):
            with patch('sitecheck.socket.getaddrinfo',return_value=[(2,1,6,'',(address,443))]):
                with self.assertRaises(ValueError): sitecheck.target('https://example.com')
        with patch('sitecheck.socket.getaddrinfo',return_value=[(2,1,6,'',('8.8.8.8',443)),(2,1,6,'',('10.0.0.1',443))]):
            with self.assertRaises(ValueError): sitecheck.target('https://example.com')
    def test_bad_scheme_port_credentials(self):
        for url in ('file:///etc/passwd','http://example.com:8090','https://user:pass@example.com'):
            with self.assertRaises(ValueError):sitecheck.target(url)
    def test_redirect_private_checked_again(self):
        calls=[]
        def transport(u,t):
            calls.append(u)
            if len(calls)==1:return 302,{'location':'http://127.0.0.1/admin'},b''
            with patch('sitecheck.socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',80))]):sitecheck.target(u)
        r=sitecheck.check('https://example.com',transport)
        self.assertEqual(r['state'],'Erro')
        self.assertIn('bloqueado',r['message'])

if __name__=='__main__':unittest.main()
