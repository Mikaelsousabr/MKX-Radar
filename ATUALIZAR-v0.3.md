# MKX Radar v0.3 — navegação e mapa

Substitua os arquivos da aplicação com os deste ZIP, preservando `gmapsdata`. Faça backup com o container parado antes de atualizar. Na pasta atual do projeto, execute:

```powershell
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081"
```

Atualize a página com Ctrl+Shift+R.

## Mudanças

- Retirados da interface os links Interface original, Documentação API e Todas as opções do motor no rodapé.
- Menu direto: Nova busca, Empresas, Análises, Mapa interativo, Funil comercial e Abordagens.
- Buscas concluídas têm Analisar e Mapa como ações diretas, além do CSV e exclusão.
- Ao abrir essas ações, a busca é importada e o painel filtra suas empresas. Não precisa copiar o ID.
- Ficha abre diagnóstico por regras automaticamente se ainda não há análise. Contém dados, evidências, serviços possíveis, anotações, histórico, etapa e análise opcional por IA.
- Mapa Leaflet/OpenStreetMap com visual ajustado, zoom, marcadores e acesso à análise individual. Empresas sem coordenadas válidas permanecem na lista.
- Mapa e lista consultam o CRM a cada 10 segundos enquanto a aba está visível. Atualizações do CRM aparecem no próximo ciclo. O enquadramento inicial não é repetido a cada atualização.
- Funil visual em colunas: abra uma empresa e altere sua etapa pela ficha.
- Abordagens leva à carteira para preparar rascunhos individuais; não envia mensagens.
- Indicador animado de solicitação e estado da coleta com contagem de buscas em execução, na fila e concluídas nesta página.
- Reimportação idêntica preserva análises existentes; dados alterados invalidam o diagnóstico anterior.

## Precisão sobre o mapa e o progresso

A base cartográfica é OpenStreetMap, não a API de mapas do Google. Os dados de empresas continuam vindo do motor de coleta do Google Maps. Tiles precisam de internet; a atribuição obrigatória do mapa permanece visível. Nenhuma chave Google é necessária nesta entrega.

O motor disponibiliza o CSV quando conclui a busca. Portanto, o mapa exibe resultados importados, não uma transmissão ponto a ponto da coleta. O status é consultado a cada 10 segundos. Não há percentual de progresso inventado.

A importação automática ocorre ao clicar Analisar/Mapa na busca concluída. Não é importação contínua de todas as buscas. Links diretos antigos da API/motor continuam funcionando, mas foram removidos da navegação.

## Validação

Seis testes passaram: regras/rascunho, validação, duplicatas/filiais, preservação de bloqueio/fontes/notas, ações de buscas concluídas e remoção de links, preservação de análise em reimportação idêntica. Integrações HTTP com motor simulado e CRM passaram. Sintaxe Python/JavaScript e ZIP conferidos.

Sem validação visual em navegador e sem build Docker real neste ambiente. A renderização do mapa e conectividade dos tiles precisam ser conferidas no seu Windows. Configuração da IA permanece no guia ATUALIZAR-v0.2.md.
