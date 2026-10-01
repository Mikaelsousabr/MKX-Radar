# MKX Radar v0.4 — verificação de sites e contatos

## Atualizar

Faça backup de `gmapsdata` com o container parado. Substitua os arquivos do projeto com este ZIP, preservando essa pasta, e execute:

```powershell
cd "C:\Users\1-03004\Downloads\MKX-Radar"
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081/empresas"
```

Atualize a página com Ctrl+Shift+R.

## Usar

Abra a ficha de uma empresa e clique em **Verificar site e contatos**. A página inicial será consultada e o relatório salvo na ficha, com data e origem. Depois, se Ollama estiver configurado, use **Analisar com IA local**: a IA receberá a coleta e as evidências desta verificação.

## O que é verificado

- Acesso HTTP, redirecionamentos e HTTPS na URL final (certificado validado durante conexão HTTPS).
- Título e descrição no HTML recebido.
- Presença de meta viewport: sinal técnico, não prova de layout mobile adequado.
- Formulários HTML, links de contato/agendamento e links WhatsApp.
- E-mails em mailto e telefones em tel. Não confirma que são válidos ou atendidos.
- Links de Instagram, Facebook, LinkedIn, TikTok e YouTube publicados pela própria página. Titularidade e atividade precisam de confirmação; links óbvios de compartilhamento são excluídos.
- Imagens no HTML e quantas não têm alt não vazio. Não diferencia imagens decorativas, nem mede qualidade de fotos ou conformidade de acessibilidade.
- Sugestões de revisão e serviços, ligadas aos sinais observados.

Estados: Verificado, Não informado, Bloqueado, Erro, Não conclusivo. Bloqueio e erro não significam ausência de site. Uma URL HTTPS com acesso bem-sucedido não comprova segurança integral do site.

## Limites

Consulta somente uma página e não executa JavaScript. Conteúdo carregado por scripts pode não aparecer. Não mede velocidade, Core Web Vitals, posicionamento no Google, qualidade visual, frequência das redes ou conversão. Não descobre sites quando o campo website está vazio. Ainda não há auditoria de fotos do Google Maps, captura de tela nem envio de mensagens.

A verificação é individual e acionada pelo usuário, com limite de tamanho, redirecionamentos e tempos de conexão/leitura. A interface permanece disponível enquanto a solicitação está em andamento. Há prevenção de acesso a endereços privados/locais: resolução DNS validada e conexão fixada no endereço público validado; cada redirecionamento é verificado novamente. Credenciais em URLs, portas diferentes de 80/443 e protocolos não HTTP/HTTPS são rejeitados.

O conteúdo extraído é mostrado como texto e usado como dados no prompt da IA. Mesmo assim, textos da IA precisam de revisão contra evidências. Não existe disparo de e-mail nesta versão.

## Validação

12 testes automatizados passaram, incluindo extração de evidências, respostas bloqueadas/erros, redirecionamentos, destinos privados, credenciais/protocolos/portas e preservação do CRM. Integração HTTP do CRM passou, inclusive a rota nova. Sintaxe Python/JavaScript e integridade do ZIP conferidas.

Build Docker real, aparência no navegador, sites reais e inferência Ollama não foram testados neste ambiente. A versão anterior foi confirmada pelo usuário no Windows.

Próxima etapa: catálogo de serviços e proposta revisável que use essas evidências; auditoria visual pode ser adicionada depois com captura de páginas e revisão humana.
