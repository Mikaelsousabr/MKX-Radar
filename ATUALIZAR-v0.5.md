# MKX Radar v0.5 — inteligência comercial

Primeiro bloco da implementação maior: triagem de oportunidades, filtros avançados e revisão humana das evidências. Os blocos de catálogo/propostas, relacionamento, automação e painel financeiro ainda não foram implementados.

## Atualizar no Windows

Pare o container antes de copiar a pasta de dados para backup. Extraia o ZIP e substitua os arquivos na pasta atual, preservando `gmapsdata`. Depois execute:

```powershell
cd "C:\Users\1-03004\Downloads\MKX-Radar"
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081/empresas?view=analysis"
```

Atualize o navegador com Ctrl+Shift+R. O banco existente ganha uma tabela de revisões automaticamente; não há necessidade de apagar dados.

## Fluxo recomendado

1. Abra a análise de uma empresa.
2. Execute Verificar site e contatos e confira as fontes no navegador.
3. No bloco Revisão da presença digital, confirme, descarte ou mantenha pendente cada hipótese.
4. Registre fontes e observações, inclusive por que o canal comercial é adequado. Confirmações exigem pelo menos 20 caracteres de evidência; esse mínimo não garante qualidade da revisão.
5. Salve a revisão. O diagnóstico consolidado mostra prioridade, pontuação explicada, serviços possíveis e próxima ação.
6. Na carteira, filtre por Prioritária para decidir quais fichas revisar antes da abordagem.

## Pontuação transparente

| Hipótese confirmada pelo usuário | Pontos |
|---|---:|
| Site não localizado após revisão | 35 |
| Melhoria de conversão identificada | 25 |
| Melhoria no Perfil da Empresa identificada | 20 |
| Canal comercial adequado revisado | 20 |

Máximo: 100. Pesos iniciais de triagem, não calibrados por vendas reais. A pontuação não prevê compra, receita ou qualidade da empresa. Não use o número como garantia de retorno.

Uma oportunidade confirmada junto de canal adequado torna a ficha Prioritária, independentemente de um corte numérico. Oportunidade sem canal revisado fica Qualificar contato. Revisão atual sem oportunidade confirmada fica Sem oportunidade confirmada. Dados sem revisão atual ficam Revisão pendente. Bloqueio de contato sempre prevalece e zera pontuação/serviços sugeridos da triagem.

Campo website vazio não recebe pontos automaticamente. Telefone ou e-mail disponível não confirma adequação, autorização ou validade do contato. Site não localizado após revisão não é afirmação universal de inexistência de site.

## Revisões e mudanças

Revisões têm data e descrição das evidências e ficam salvas no banco. Mudança na coleta ou no resultado da verificação do site torna a revisão desatualizada: suas respostas permanecem disponíveis para revisão, mas deixam de contar na pontuação. Reimportação idêntica, mudança de etapa comercial ou só da data da mesma verificação não invalidam a revisão.

O diagnóstico da IA opcional agora recebe também a triagem/revisão. O texto continua precisando de revisão humana. Não há avanço automático de etapa nem envio de mensagens.

## Filtros e exportação

- Prioridade comercial.
- Revisão atualizada, pendente ou desatualizada.
- Contato disponível ou não encontrado nos campos coletados.
- Estado técnico do site: verificado, bloqueado, erro, não informado, não conclusivo ou não analisado.
- Ordenação por pontuação, nome ou atualização recente.
- Filtros anteriores por texto, etapa e site preservados.
- Contadores refletem o filtro aplicado e, ao abrir uma busca específica, somente suas empresas.
- CSV do CRM agora contém prioridade, pontuação, estado da revisão e próxima ação. Exportação inclui a carteira inteira; os filtros da tela não limitam o CSV nesta versão.

## Validação

19 testes automatizados passaram. Novos testes cobrem prioridade sem revisão, pontos explicados, bloqueio, persistência/invalidação de revisões, validações e alterações nas evidências do site. Integração HTTP passou para importação, análise, verificação, revisão, triagem, bloqueio e exportação. Sintaxe Python/JavaScript e ZIP conferidos.

Não foram executados build Docker real, validação visual em navegador ou inferência Ollama neste ambiente. As versões anteriores foram confirmadas no Windows pelo usuário.

Próximo bloco: catálogo de serviços, preços editáveis e propostas revisáveis com evidências da oportunidade.
