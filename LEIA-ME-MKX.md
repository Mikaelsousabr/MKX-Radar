# MKX Radar — base inicial

Encontre empresas. Descubra oportunidades.

Este pacote contém o código-fonte completo do scraper original, sem personalização visual ainda. A licença MIT e os créditos foram preservados. Não inclui executável Windows nem histórico .git.

## Enviar ao GitHub
Extraia o ZIP. Abra a pasta MKX-Radar, selecione todo o conteúdo (incluindo as pastas ocultas .github e arquivos .gitignore) e envie em Add file > Upload files no repositório Mikaelsousabr/MKX-Radar. Não envie apenas o ZIP: o GitHub não o extrai.

## Executar o código deste pacote
Com Docker Desktop aberto em modo Linux, abra PowerShell dentro da pasta extraída:

```powershell
docker build -t mkx-radar:local .
New-Item -ItemType Directory -Force gmapsdata | Out-Null
docker run --rm --name mkx-radar -p 127.0.0.1:8081:8080 --mount "type=bind,source=$($PWD.Path)\gmapsdata,target=/gmapsdata" -e DISABLE_TELEMETRY=1 mkx-radar:local -web -data-folder /gmapsdata -c 2
```

Abra http://localhost:8081. No campo de idioma use pt, não pt-BR. A porta 8081 permite manter o scraper anterior na porta 8080. A construção depende da disponibilidade do Go 1.27.1 e das versões de dependências declaradas no go.mod; não foi testada neste ambiente.

README.md contém a documentação completa do projeto original.
