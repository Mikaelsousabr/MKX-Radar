# MKX Radar v0.10 — interface limpa e IA local

## Atualizar

Faça backup de `gmapsdata` com o container parado. Substitua os arquivos com o ZIP, preservando essa pasta, e execute:

```powershell
cd "C:\Users\1-03004\Downloads\MKX-Radar"
docker compose -f compose.mkx.yaml up -d --build
Start-Process "http://localhost:8081"
```

Atualize com Ctrl+Shift+R.

## Interface

- Fotos deixam de aparecer como JSON e ganham galeria (até oito imagens, quando disponíveis).
- URLs completas do site/Maps viram botões com rótulos legíveis.
- Nota aparece com uma casa decimal, junto da quantidade de avaliações.
- Dados brutos/JSON deixam de aparecer na ficha; o histórico de atividades permanece.
- Horários coletados aparecem em formato legível quando o conteúdo é reconhecido.
- IDs técnicos das buscas deixam de aparecer como coluna da lista.
- Importação por ID fica oculta na interface; importação automática, análise das buscas e importação CSV continuam disponíveis.
- Na fila, resultados JSON viram resumo de empresas novas/atualizadas ou resultado da consulta do site. Destinos mostram o nome da empresa ou Busca concluída, sem ID técnico.
- A ficha tem mais espaço e cabeçalho fixo para fechar sem voltar ao topo.

Dados completos permanecem no banco e nas exportações originais. As URLs continuam funcionando internamente. Identificadores curtos de propostas e referências financeiras permanecem como controles de negócio; não são código executável.

Fotos dependem da disponibilidade dos links e da conexão. Apenas imagens HTTPS hospedadas no Googleusercontent são usadas na galeria nesta versão. Falhas mostram Foto indisponível. Isso não é análise visual das fotos.

## Usar seu Ollama

1. Abra o Ollama no Windows.
2. No menu do MKX, abra **IA local**.
3. Clique **Buscar modelos instalados**.
4. Escolha um modelo de conversa que já está disponível na sua máquina.
5. Clique **Usar este modelo**, depois **Testar IA**.
6. Na ficha de empresa, clique **Analisar com IA local**.

O modelo selecionado fica no banco; não exige alterar o Compose ou recriar o container a cada escolha. Selecionar Análise por IA desativada tem prioridade sobre configurações antigas de ambiente. O diagnóstico por regras continua funcionando.

Não sabemos o nome do modelo instalado ontem sem consultar seu Ollama. O app não instala ou baixa modelos, não pede chave de API e não oferece modelos identificados como remotos/cloud na lista. Modelos de embeddings não servem para este diagnóstico; escolha um modelo de conversa e confirme pelo teste.

A primeira geração pode demorar até o modelo carregar. A análise recebe dados relevantes da empresa, evidências técnicas e revisão comercial. Não navega por sites nem substitui revisão humana.

## Se o Docker não conseguir conectar

A API do Ollama escuta em localhost por padrão. O Docker precisa conseguir acessar essa API no Windows.

- Encerre o Ollama pelo ícone perto do relógio (Quit/Encerrar).
- Execute `Conectar-IA-Local.bat` da pasta do projeto. Ele inicia uma instância com acesso para o Docker, sem alterar permanentemente as variáveis do Windows.
- Mantenha a janela aberta. Se disser que a porta está em uso, ainda há uma instância do Ollama rodando; não precisa desinstalar nada.
- Restrinja a porta 11434 ao ambiente local/Docker no firewall; não a libere publicamente.
- Volte à tela IA local e tente Buscar modelos instalados.

O auxiliar não baixa modelos nem encerra processos existentes. Desativa recursos cloud naquela instância. Para encerrar a instância, use Ctrl+C. Ao abrir o Ollama normalmente outra vez, os ajustes temporários do auxiliar não são herdados.

Referências oficiais: https://docs.ollama.com/api/tags e https://docs.ollama.com/faq (configuração Windows, OLLAMA_HOST e OLLAMA_NO_CLOUD).

## Validação

57 testes automatizados passaram. Novos testes cobrem lista de modelos locais, seleção persistente, desativação, modelos inexistentes, conexão indisponível, geração, preservação de evidências e remoção de blocos brutos/IDs na interface. Integração HTTP passou com Ollama simulado para tela, lista, seleção e teste. Sintaxe Python/JavaScript e ZIP conferidos.

Não houve inspeção visual em navegador, build Docker real nem inferência no Ollama da sua máquina. A conexão/modelo precisam do seu teste local. Não afirmamos ter acessado seu Windows ou visto qual modelo está instalado.
