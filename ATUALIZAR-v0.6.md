# MKX Radar v0.6 — catálogo MKX e propostas

Segundo bloco da implementação maior. Serviços e propostas agora ficam no banco local, junto ao CRM.

## Atualizar

Faça backup da pasta `gmapsdata` com o container parado. Substitua os arquivos do projeto com este ZIP, preservando a pasta de dados, e execute:

```powershell
cd "C:\Users\1-03004\Downloads\MKX-Radar"
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081/comercial"
```

Atualize com Ctrl+Shift+R. As novas tabelas são criadas sem apagar o banco existente.

## Primeiro uso

1. Abra **Serviços MKX** no menu. Edite os preços, escopos, condições e prazos sugeridos.
2. Existem seis serviços iniciais: site institucional, página de conversão, Perfil da Empresa no Google, conteúdo/redes, tráfego e automação/IA. Os preços começam zerados para você definir; não são recomendações de preço.
3. Abra uma empresa com revisão atualizada e clique em **Criar proposta**, ou vá em Propostas > Nova proposta.
4. Selecione os serviços, personalize entregáveis e valores para aquele cliente. Prazo do catálogo é apenas sugestão para editar; não é uma data de entrega calculada.
5. Revise o contexto da oportunidade, prazo e condições comerciais. Evidências humanas são preenchidas quando há revisão atual e serviços ligados à oportunidade; podem e devem ser adaptadas para o cliente.
6. Salve como Rascunho. Depois da revisão, marque Pronta. Essa marcação exige preços positivos, contexto com pelo menos 20 caracteres, prazo, condições e revisão atualizada da empresa.
7. Use **Imprimir / PDF da revisão salva**. Na impressão do navegador, escolha Salvar como PDF. O app gera HTML para impressão; não cria automaticamente um arquivo PDF no servidor.

## Recursos entregues

- Catálogo editável: nome, objetivo, escopo, exclusões/pré-requisitos, preço, cobrança única/mensal e prazo sugerido.
- Adicionar novos serviços e desativar serviços sem afetar propostas anteriores.
- Propostas vinculadas às empresas, com escopo e preço próprios para cada item.
- Totais separados de serviços únicos e mensais. Não soma mensalidades como se fossem pagamento único.
- Valores calculados em centavos no servidor, com validação de preço.
- Contexto, prazo e condições comerciais editáveis.
- Cada salvamento cria uma revisão imutável; revisões anteriores podem ser abertas e impressas.
- Alteração no catálogo não modifica propostas salvas.
- Proteção contra edição simultânea: uma revisão antiga não sobrescreve a nova. Reabra a revisão mais recente antes de salvar novamente.
- Status: Rascunho, Pronta, Enviada manualmente, Aceita registrada, Recusada registrada.
- Eventos no histórico da empresa e armazenamento de evidências da revisão junto à proposta.
- Empresa bloqueada para contato não permite criar ou alterar propostas. Propostas anteriores permanecem consultáveis para histórico interno.

## Limites importantes

Enviada e Aceita são registros manuais; não comprovam envio, resposta ou assinatura. Nenhuma mensagem é enviada. O sistema não muda automaticamente a etapa do CRM nem registra receita recebida.

A proposta pode incluir evidências sensíveis ou anotações internas se você as copiar para o contexto: revise antes de imprimir ou compartilhar. A página de impressão mostra somente os campos da proposta, não o histórico completo da empresa nem o prompt da IA.

PDF é salvo pela impressão do navegador. Links localhost são locais e não funcionam para um cliente remoto; compartilhe o PDF depois de revisá-lo. As versões ficam no banco local e não são publicadas na internet.

Documentos salvos preservam o contexto daquela revisão. Dados novos da empresa não atualizam propostas automaticamente. Ao abrir a proposta, o painel mostra o estado atual da revisão comercial da empresa para você conferir.

Próximos blocos: relacionamento (próxima ação, lembretes e acompanhamento), automação local de importações/verificações e painel de resultados.

## Validação

26 testes automatizados passaram, incluindo valores exatos, validação, totais, revisões, conflitos entre abas, preços do catálogo sem alteração em propostas antigas, bloqueio, exigências para proposta pronta e escape de HTML na impressão. Integração HTTP nova passou para catálogo, propostas, revisões, impressão histórica e listagem. Sintaxe Python/JavaScript, IDs únicos da página e ZIP conferidos.

Sem build Docker real, inspeção visual no navegador ou geração real de PDF neste ambiente. Esses pontos precisam da sua execução no Windows.
