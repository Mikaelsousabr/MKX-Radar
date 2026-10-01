# MKX Radar v0.2 — central de empresas

## Atualizar no Windows

1. Feche abas do painel durante a atualização.
2. Faça uma cópia de segurança da pasta `gmapsdata`, com o container parado.
3. Extraia este ZIP em uma pasta temporária. Copie os arquivos para a pasta existente `C:\Users\1-03004\Downloads\MKX-Radar`, substituindo arquivos. O ZIP não contém `gmapsdata`: preserve sua pasta de dados.
4. Execute no PowerShell:

```powershell
cd "C:\Users\1-03004\Downloads\MKX-Radar"
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081/empresas"
```

Para parar antes do backup:

```powershell
docker compose -f compose.mkx.yaml stop
Copy-Item .\gmapsdata .\gmapsdata-backup-v01 -Recurse
```

Use outro nome de backup caso esse já exista. Não exclua gmapsdata e não exponha a porta na internet.

## Primeiro uso

- Em Central de buscas, termine uma busca e copie o ID.
- Em Empresas e oportunidades, cole o ID e clique em Importar busca. Alternativamente, importe o CSV baixado do motor.
- Abra a ficha e execute Diagnóstico por regras.
- Confira as fontes, visite o site/Google Maps e registre sua revisão nas anotações.
- Mova a etapa comercial. Gere um rascunho de abordagem somente quando o contato for adequado.
- Exporte o CSV para conferir seu funil.

## Entregue nesta versão

- Marca MKX Soluções com link para https://mkxsolucoes.com.
- Painel de empresas, filtros por texto, etapa e site informado.
- Importação por ID da busca ou arquivo CSV, limite 10 MB.
- Banco SQLite persistente `gmapsdata/mkx-crm.sqlite`; não depende da memória do container.
- Deduplicação por place_id/data_id/cid; fallback conservador por nome, endereço e coordenadas. Mudanças desses campos sem identificador estável podem gerar duplicata. Revisão humana ainda necessária.
- Fontes de origem, histórico, notas e funil comercial.
- Site, telefone, e-mails, nota, avaliações, dados brutos de fotos quando disponíveis e link do Maps.
- Diagnóstico por regras, com evidências e serviços possíveis.
- IA textual local opcional via Ollama, sem necessidade de chave paga.
- Rascunho de e-mail com identidade da MKX e pedido de preferência. Nenhum e-mail é enviado pelo app.
- Bloqueio permanente de contato por empresa nesta versão, preservado nas reimportações. Não é supressão global por endereço de e-mail: isso pertence à futura camada de envio.
- Exportação do CRM com proteção contra fórmulas em planilhas.

## IA local opcional

Sem configuração, o diagnóstico por regras funciona normalmente. Para habilitar IA, instale Ollama no Windows e baixe um modelo compatível com os recursos do seu PC (por exemplo `ollama pull qwen2.5:3b`). O download pode ocupar vários GB. Esta integração espera a API do Ollama em `host.docker.internal:11434` a partir do container.

O Ollama precisa aceitar conexão do Docker. Caso esteja escutando apenas em localhost, encerre o processo existente e configure `OLLAMA_HOST=0.0.0.0:11434` antes de iniciá-lo. Restrinja o acesso no firewall ao ambiente local/Docker; não abra essa API na internet. A configuração depende da instalação do Ollama no seu Windows.

No PowerShell da pasta do projeto:

```powershell
$env:MKX_OLLAMA_MODEL = "qwen2.5:3b"
docker compose -f compose.mkx.yaml up -d --build
```

Depois, abra uma ficha e clique em Analisar com IA local. O modelo é passado pelo Compose ao container. Para persistir entre terminais, crie `.env` ao lado do Compose contendo `MKX_OLLAMA_MODEL=qwen2.5:3b`.

A IA recebe os dados coletados daquela empresa, usa limite de geração e pode demorar até dois minutos. Respostas precisam de revisão. A instalação, conectividade e inferência real do Ollama não foram testadas neste ambiente.

## Limites explícitos e evolução

Esta é a primeira entrega do plano v2. Ainda não há rastreamento automático de redes sociais, auditoria HTTP/visual do site, análise das fotos, comparação de concorrentes, captura mobile, catálogo de preços/propostas em PDF ou disparo/sequência de e-mails. A importação é acionada pelo usuário; não ocorre automaticamente ao terminar uma busca.

Site ausente no CSV é informação pendente, não prova de ausência real. Número de telefone não confirma WhatsApp. O app não rotula empresas como amadoras nem inventa faturamento ou oportunidades perdidas. A IA não navega nos sites nesta versão.

Próxima entrega recomendada: verificação de site e contatos com evidência, data e resultado (confirmado, não encontrado, bloqueado ou erro), seguida de catálogo de ofertas. Envios exigem infraestrutura de e-mail, identidade do remetente, revisão de contatos e mecanismo persistente de descadastro acessível mesmo com o PC desligado.

## Validação desta entrega

- Quatro testes automatizados: deduplicação, preservação de bloqueio/notas/fontes, separação de filiais, validações e diagnóstico/rascunho.
- Integração HTTP com motor simulado: rotas originais, formulários, traduções, downloads e assets.
- Integração HTTP do CRM: importação, ficha, diagnóstico, bloqueio, rascunho e exportação.
- Sintaxe Python e JavaScript e integridade do ZIP.
- Sem Docker/Go neste ambiente: build real no Windows e aparência no navegador precisam da sua execução. Motor Go original não foi alterado.

Licenças MIT do motor e das bibliotecas permanecem nos arquivos correspondentes.
