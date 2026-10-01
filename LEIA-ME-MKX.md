# MKX Radar — versão local 0.1

Encontre empresas. Descubra oportunidades.

## Iniciar no Windows

1. Extraia a pasta MKX-Radar do ZIP em C:\IA\MKX-Radar (não execute dentro do ZIP).
2. Abra o Docker Desktop e aguarde o motor Linux ficar ativo.
3. Dê dois cliques em **Iniciar-MKX-Radar.bat**.
4. Aguarde a construção inicial. O navegador abrirá http://localhost:8081.

Você pode fechar a janela do iniciador depois de iniciar. Mantenha o Docker Desktop aberto. O painel usa a porta 8081; o scraper anterior pode continuar na porta 8080.

Os dados ficam na subpasta **gmapsdata**, junto aos scripts. Faça backup dessa pasta. Não apague os dados para atualizar a interface.

Use **Parar-MKX-Radar.bat** para parar e **Logs-MKX-Radar.bat** para acompanhar os logs. Por usar restart: unless-stopped, o serviço pode voltar a iniciar quando o Docker reiniciar; use o script de parada para desativá-lo.

## Primeira busca

- Nome: Dentistas Sobral.
- Busca: dentistas em Sobral Ceará.
- Idioma: Português (pt).
- Profundidade: 1.
- Sem modo rápido, e-mails ou proxy no primeiro teste.

Acompanhe o status. Quando concluir, baixe o CSV e confira se há empresas. Status concluído não garante resultados. Para importar no Excel, use Dados > De Texto/CSV, UTF-8 e separador vírgula.

## O que mudou

- Painel MKX escuro, azul e verde, adaptado ao celular.
- Criação, atualização, exclusão, visualização no mapa e download de buscas.
- Campos e status em português.
- Idioma pt por padrão e normalização de pt-BR na submissão do formulário.
- Erros exibidos de forma legível e bloqueio de duplo envio.
- Bibliotecas HTMX e Leaflet servidas localmente. Os mapas e a coleta continuam precisando de internet.
- Interface original acessível pelo menu para preservar suas opções.

## Arquitetura e funções preservadas

Dockerfile.mkx reaproveita a imagem publicada gosom/google-maps-scraper:latest e acrescenta um gateway Python, usando apenas a biblioteca padrão. Esse gateway serve a nova interface e encaminha as rotas e API ao motor na porta interna 8090. O navegador fala somente com a porta 8081 no Windows, vinculada a 127.0.0.1, sem expor o painel à rede.

O código-fonte original e a licença MIT continuam no pacote. O motor em execução vem da imagem publicada, não de uma recompilação desse código. O Dockerfile original continua disponível para quem quiser compilar o fonte; ele exige Go 1.27.1. O novo iniciador não depende dessa compilação.

Todas as funções do motor continuam disponíveis: CLI, JSON/CSV, retomada, extração de e-mails, avaliações adicionais, grid, proxies, PostgreSQL, exportação LeadsDB e modos avançados. Nem todas têm controles no novo painel; use CLI/API/documentação original para elas. Não foi criado um CRM, login multiusuário nem uma integração Vercel.

Para consultar as opções CLI do mesmo motor:

```powershell
docker run --rm --entrypoint google-maps-scraper mkx-radar:local -h
```

API local: http://localhost:8081/api/docs. README-UPSTREAM.md contém a documentação original.

## Executar manualmente

Abra PowerShell nesta pasta:

```powershell
docker compose -f compose.mkx.yaml up -d --build
```

Para parar:

```powershell
docker compose -f compose.mkx.yaml stop
```

Se a porta 8081 estiver ocupada, edite compose.mkx.yaml e os dois endereços em Iniciar-MKX-Radar.ps1 para outra porta. Concurrency começa em 2 e pode ser alterada no compose (MKX_CONCURRENCY). Aumentar pode consumir mais RAM e causar bloqueios.

A primeira construção precisa de internet para baixar a imagem Docker e instalar Python. A tag latest pode mudar; o uso local posterior reaproveita a imagem já construída. Para atualizar explicitamente a base, use docker compose -f compose.mkx.yaml build --pull, depois up -d.

## GitHub

Envie os arquivos extraídos, incluindo mkx/, Dockerfile.mkx, compose.mkx.yaml e os iniciadores. Não envie somente o ZIP. Não publique gmapsdata nem credenciais de proxy. Este pacote é para Docker local; não o implante diretamente na Vercel.

## Validação e limites

Verificações HTTP do gateway usam um motor simulado para testar rotas, normalização do formulário, downloads e erros. A sintaxe Python/JavaScript e a configuração Compose foram verificadas. A inspeção em navegador não pôde ser concluída neste ambiente. A coleta real e a construção Docker precisam ser confirmadas no seu Windows; o ambiente de produção deste pacote ainda não foi executado aqui.

## Créditos e licenças

Base: gosom/google-maps-scraper, licença MIT em LICENSE. Biblioteca HTMX: BSD-2-Clause (mkx/static/vendor/HTMX-LICENSE). Leaflet: BSD-2-Clause (mkx/static/vendor/LEAFLET-LICENSE). Personalização MKX Radar para Mikael Sousa.
