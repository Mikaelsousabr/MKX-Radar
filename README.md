# MKX Radar v0.4

Verificação de sites, contatos e redes vinculadas. Guia atual: [ATUALIZAR-v0.4.md](ATUALIZAR-v0.4.md).

# MKX Radar v0.3

Navegação direta, análise das buscas e mapa interativo. Instruções: [ATUALIZAR-v0.3.md](ATUALIZAR-v0.3.md).

# MKX Radar v0.2

Central local de empresas, oportunidades e CRM. Consulte [ATUALIZAR-v0.2.md](ATUALIZAR-v0.2.md) para instalar, atualizar e configurar IA opcional.

# MKX Radar

**Encontre empresas. Descubra oportunidades.**

Plataforma local de prospecção com painel em português, baseada no projeto open source [gosom/google-maps-scraper](https://github.com/gosom/google-maps-scraper).

## Windows + Docker

Extraia os arquivos, abra o Docker Desktop e execute **Iniciar-MKX-Radar.bat**. Acesse http://localhost:8081.

Ou execute:

```powershell
docker compose -f compose.mkx.yaml up -d --build
```

Leia [LEIA-ME-MKX.md](LEIA-ME-MKX.md) para instalação, funções, arquitetura e limites. A documentação original permanece em [README-UPSTREAM.md](README-UPSTREAM.md). A licença MIT original permanece em [LICENSE](LICENSE).

O novo painel utiliza o motor Docker publicado. CLI, API e funções avançadas permanecem acessíveis. A versão atual é para execução local; não está adaptada para Vercel.
