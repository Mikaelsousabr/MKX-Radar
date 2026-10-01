# MKX Radar v0.8 — automação e fila persistente

Quarto bloco da implementação maior: importação automática e fila de verificações locais. Não envia mensagens.

## Atualizar

Faça backup de `gmapsdata` com o container parado. Substitua os arquivos do projeto pelo conteúdo deste ZIP, preservando a pasta de dados. Execute:

```powershell
cd "C:\Users\1-03004\Downloads\MKX-Radar"
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081/automacoes"
```

Atualize com Ctrl+Shift+R. O banco ganha tabelas da fila/configurações automaticamente.

## Como usar

- A importação automática começa ativada na primeira instalação desta versão. Ela também encontra buscas concluídas anteriormente no motor, não apenas as novas. Pode desativar em Automação e fila.
- Verificação automática dos sites começa desativada. Ative **Verificar sites após importações automáticas** e salve opções se desejar.
- Essa opção vale para importações executadas pela fila depois da ativação. Para empresas já importadas, aplique filtros na carteira e clique em **Verificar empresas deste filtro**.
- Empresas sem site informado ou bloqueadas para contato são ignoradas no lote. Cada solicitação aceita até 1000 empresas; refine os filtros para lotes maiores.
- Também pode adicionar uma importação por ID de busca concluída.
- Acompanhe as tarefas em Automação e fila. Falhas permitem repetição manual até 3 tentativas por tarefa. Não há repetição automática infinita.

## Execução

Um worker processa uma tarefa por vez: importação ou verificação. Consulta o motor aproximadamente a cada 15 segundos quando não estiver pausado. Uma verificação longa pode adiar a próxima consulta; não é intervalo de tempo real rígido.

O painel da fila consulta o estado a cada 5 segundos enquanto estiver visível. O worker continua rodando com a aba fechada enquanto o Docker permanecer ativo.

Configurações, resultados, falhas, contagem de tentativas e tarefas ficam no SQLite persistente em `gmapsdata`. Tarefas marcadas Executando no encerramento inesperado voltam para Pendente ao reiniciar, respeitando o limite de tentativas. Processamento pode repetir a etapa interrompida; importação deduplica as empresas e verificações podem ser executadas novamente.

Buscas são importadas uma vez por ID pela fila. Empresas e tarefas já ativas são deduplicadas. Importação manual anterior não preenche o histórico da fila, portanto pode haver uma importação adicional sem duplicar empresas. Empresas coletadas com dados alterados podem gerar uma nova verificação automática; isso não substitui revisão humana.

Pausar impede novas consultas automáticas e novas execuções. Você ainda pode adicionar itens que ficarão pendentes. Uma tarefa em execução termina normalmente; não há cancelamento forçado. Pode cancelar tarefas Pendentes. Bloqueio de contato é conferido antes de iniciar a verificação.

## Progresso e estados

- Pendente: aguardando o worker.
- Executando: tarefa assumida pelo worker.
- Concluída: operação terminou; confira o resultado. Um site Bloqueado/HTTP 403 pode concluir a consulta sem ter sido auditado.
- Falhou: erro de operação ou site classificado Erro.
- Cancelada: cancelamento explícito ou empresa bloqueada antes da execução.

Percentual = tarefas tratadas / total da fila. Tratadas inclui Concluída, Falhou e Cancelada; não é taxa de sucesso. Totais incluem todo o histórico da fila; lista mostra as últimas 300 tarefas. O percentual pode diminuir quando novos itens entram.

Não há percentual interno inventado de uma página sendo consultada. O motor libera resultados após concluir a busca; não é transmissão contínua de empresas durante a coleta.

## Limites

A fila não faz análise visual, não executa JavaScript e não roda IA em lote nesta versão. Ela usa a mesma verificação de página inicial já entregue, com seus limites e proteção de destinos. Nunca tenta contornar bloqueios do site.

As falhas não são repetidas automaticamente. Após 3 tentativas de importação com erro, pode importar o CSV pela carteira após corrigir a causa. Para uma nova rodada de verificação, selecione as empresas novamente na carteira. Tarefas duplicadas ativas continuam impedidas.

O funcionamento depende do Docker aberto e da internet para consultar os sites. Parar Docker suspende a execução; trabalhos interrompidos são recuperados no próximo início.

## Validação

43 testes automatizados passaram. Novos testes cobrem importação de buscas concluídas, deduplicação, pausa, retomada após interrupção, falhas/tentativas, lotes, bloqueios, estados e progresso. Integração HTTP com motor simulado passou para consulta, importação, lote de verificação, pausa, cancelamento e painel. Integração de relacionamento também passou; sintaxe Python/JavaScript e ZIP conferidos.

Não foram executados build Docker real, inspeção visual no navegador ou lote contra sites reais neste ambiente. Valide esses pontos no seu Windows.

Próximo bloco: painel de resultados comerciais, com empresas qualificadas, contatos, propostas, vendas registradas e valores separados de receitas efetivamente recebidas.
