# MKX Radar v0.9 — resultados comerciais

Quinto bloco da implementação maior: visão geral, atividade por período e movimentos de caixa informados. Os cinco blocos agora estão implementados: inteligência comercial, ofertas/propostas, relacionamento, automação local e painel de resultados. Auditoria visual e envio automático continuam fora desta entrega.

## Atualizar no Windows

Faça backup de `gmapsdata` com o container parado. Substitua os arquivos pelo ZIP, preservando essa pasta. Execute:

```powershell
cd "C:\Users\1-03004\Downloads\MKX-Radar"
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081/resultados"
```

Atualize com Ctrl+Shift+R. As novas tabelas são adicionadas ao banco sem apagar os registros anteriores.

## O painel mostra

### Carteira atual

Empresas, prioritárias, ganhas no CRM, bloqueadas e distribuição por etapa. Esses indicadores não são filtrados pelo período; representam o estado atual. Ganhas no CRM são empresas marcadas manualmente na etapa Ganha, não propostas aceitas nem recebimentos.

### Atividade no período

Empresas únicas com contato registrado, resposta registrada e reunião registrada; propostas cuja última revisão está dentro do período. Datas das interações são datas de registro, não necessariamente da conversa original. Uma empresa com vários contatos conta uma vez em cada indicador. Não há taxa de resposta/conversão calculada a partir de grupos de períodos diferentes.

### Propostas atuais

Valores das propostas aceitas registradas e das propostas prontas/enviadas manualmente, sempre pela revisão mais recente e sem duplicar revisões antigas. Valores únicos e mensais permanecem separados. As somas representam as propostas atuais de toda a carteira; o filtro de data não limita esse bloco. Não equivalem a receita recebida nem a previsão de vendas.

### Caixa informado no período

Recebimentos, estornos, saldo dos movimentos e quantidade de movimentos válidos. Filtrados pela data informada de cada movimento. Gráfico apresenta o líquido de cada dia com registros (dias sem movimento não são desenhados). Não há cálculo de lucro, despesas, impostos ou conciliação bancária.

### Próximas ações

Até 12 tarefas pendentes mais próximas, com atrasos destacados. Não são limitadas pelo filtro de período. Agenda completa continua disponível.

## Registrar movimentos

1. Selecione a empresa e, opcionalmente, a proposta correspondente.
2. Escolha Recebimento ou Estorno, informe valor e data ocorrida (não futura).
3. Informe referência única para aquele movimento, empresa e tipo. Exemplos: identificador da transação ou número interno de controle; use referências distintas para parcelas distintas.
4. Confira os dados e marque a confirmação antes de salvar. O app registra sua declaração, não verifica o banco.
5. Para devolução real de dinheiro, registre Estorno. Para um lançamento feito por engano, use Anular lançamento incorreto com justificativa. A anulação mantém os dados originais e deixa de incluí-los nos totais.

Valores são calculados em centavos no servidor. O mesmo ID de uma requisição repetida não cria duplicata. Referências ativas iguais para empresa/tipo são impedidas. Proposta vinculada precisa pertencer à empresa.

Não existe edição destrutiva nem exclusão dos movimentos pelo painel. Anulações geram evento no histórico da empresa e preservam justificativa. Movimentos de empresas bloqueadas podem ser registrados para documentação financeira interna; isso não desbloqueia contato.

## Exportar

Exportar movimentos CSV respeita o período selecionado e inclui lançamentos anulados com status/motivo. Totais do painel excluem anulados. Colunas textuais têm proteção contra fórmulas em planilhas. Dados e valores vêm exclusivamente dos registros manuais do app.

O período padrão é de 30 dias, incluindo hoje. Atividades são agrupadas no fuso America/Fortaleza (-03:00). Painel consulta atualizações a cada 30 segundos enquanto visível.

## Validação

51 testes automatizados passaram. Novos testes cobrem valores aceitos sem geração indevida de caixa, revisões sem dupla contagem, recebimentos, estornos, correções, IDs/referências duplicados, fuso/período, confirmação e datas futuras, vínculos de propostas e proteção do CSV. Integração HTTP passou para painel, registro, totais exatos, exportação por período e anulação. Sintaxe Python/JavaScript e ZIP conferidos.

Não foram executados build Docker real ou inspeção visual de navegador neste ambiente. Valide no seu Windows. Não há integração bancária, fiscal ou de pagamentos.

## Piloto recomendado

Faça uma busca pequena, revise cinco empresas, gere uma proposta, registre um contato e agende uma próxima ação. Só registre valores realmente recebidos ou devolvidos. Compare os indicadores com os registros para confirmar que o fluxo funciona na sua rotina antes de aumentar os lotes.
