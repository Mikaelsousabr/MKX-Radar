# MKX Radar v0.7 — relacionamento e agenda comercial

Terceiro bloco da implementação maior: próximas ações, agenda e histórico de contatos. Tudo permanece local; não envia mensagens.

## Atualizar

Faça backup de `gmapsdata` com o container parado. Substitua os arquivos pelo conteúdo do ZIP preservando essa pasta. Depois execute:

```powershell
cd "C:\Users\1-03004\Downloads\MKX-Radar"
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081/relacionamento"
```

Atualize com Ctrl+Shift+R. As novas tabelas são adicionadas ao banco sem apagar as anteriores.

## Fluxo de uso

1. Na ficha de uma empresa, clique em **Contato e próxima ação**.
2. Agende uma ação com título, data/hora e contexto.
3. Após conversar, registre contato, resposta, reunião, proposta apresentada ou nota interna.
4. Conclua a tarefa e agende o próximo passo. A etapa do CRM continua editável pela ficha e não muda automaticamente por esses registros.
5. Se a empresa recusar novos contatos, registre **Recusa / descadastro**. Isso bloqueia permanentemente o contato e cancela todas as tarefas pendentes daquela empresa.

## Entregue

- Menu Agenda comercial e Abordagens com acesso direto ao relacionamento.
- Agenda por empresa, tarefas pendentes, atrasadas, do dia, concluídas e canceladas.
- Contadores e atualização das tarefas a cada 30 segundos enquanto a aba estiver visível.
- Criar, concluir, cancelar ou reagendar próxima ação.
- Controle de revisão para impedir que uma edição antiga sobrescreva alterações de outra aba.
- Datas armazenadas em UTC. Agenda exibida no fuso America/Fortaleza; campos e reagendamento interpretam o horário no fuso do navegador do usuário.
- Registros de contatos e respostas com canal, texto e data do registro.
- IDs dos registros de interação impedem duplicação da mesma requisição em uma tentativa repetida.
- Histórico de até 500 interações, filtrado por empresa; eventos também entram no histórico da ficha.
- Registro atômico de recusa, bloqueio e cancelamento de tarefas pendentes.
- Bloquear pela ficha do CRM também cancela tarefas pendentes.
- Rascunhos de e-mail e WhatsApp ligados a serviços sugeridos em revisão atualizada, com oportunidade e canal comercial confirmados.

## Limites

Os lembretes são alertas visuais da agenda. Com o painel fechado não existem notificações externas, e com o Docker parado não existe consulta do app. Não é uma automação do calendário nem um lembrete do ChatGPT.

Histórico usa a data do registro; nesta versão não há campo separado para a data original da conversa. O histórico pode receber registros antigos de uma empresa bloqueada, para documentação interna, mas isso não libera contato nem permite nova tarefa.

Respostas são registradas manualmente; não existe sincronização de caixa de e-mail/WhatsApp. Registro de resposta não cancela automaticamente as tarefas: conclua ou reagende cada ação. Recusa/descadastro cancela tarefas automaticamente por segurança.

Os rascunhos não são enviados. Adapte com observação específica, identidade pessoal e destinatário correto. O contato revisado no app não substitui análise de adequação da abordagem. Alterações no texto do rascunho não são persistidas nesta versão: copie o texto que desejar utilizar.

Nenhuma interação muda automaticamente as etapas do CRM ou os status das propostas. Os registros não comprovam envio, aceite ou receita recebida.

## Validação

33 testes automatizados passaram, incluindo fuso/atraso, conclusão, conflito entre edições, recusas/bloqueios, cancelamento de tarefas, repetição de registros, rascunhos condicionados à revisão e preservação em reimportações. Integrações HTTP do relacionamento e propostas passaram. Sintaxe Python/JavaScript e integridade do ZIP conferidas.

Sem build Docker real ou inspeção visual de navegador neste ambiente; precisam da sua validação no Windows.

Próximo bloco: automação local de importação de buscas concluídas, fila de verificações e acompanhamento de falhas/progresso real. Depois, painel consolidado de resultados comerciais.
