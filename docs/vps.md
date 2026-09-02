# Acesso E Operacao Na VPS

O Limulus roda 24/7 na mesma VPS do projeto Nautilus. O banco vivo da VPS e a
fonte da verdade e nao deve ser substituido pelo banco de uma copia local.

Os dados concretos de conexao ficam em `.vps.yml`, na raiz do repositorio. Esse
arquivo e ignorado pelo Git porque o repositorio e publico. O modelo versionado
fica em [`config/vps.exemplo.yml`](../config/vps.exemplo.yml). Chaves privadas,
senhas, tokens e conteudo de `.env` nunca devem ser copiados para Markdown ou
YAML versionado.

## Procedimento Para Agentes De IA

Antes de qualquer operacao remota:

1. Ler `.vps.yml` e validar `conexao.alias_ssh`, `conexao.host`,
   `conexao.usuario`, `conexao.porta` e `conexao.identidade_ssh`.
2. Testar acesso somente leitura com `ssh vps-limulus`. Se o alias nao estiver
   disponivel, usar explicitamente host, usuario, porta e chave configurados.
3. Confirmar no servidor o diretorio e o servico configurados antes de executar
   comandos que alterem arquivos ou reiniciem processos.
4. Fazer backup do SQLite vivo com `gerenciar_dados.py backup` antes de deploys
   que alterem esquema, persistencia ou migracoes.
5. Atualizar codigo com fast-forward e preservar `.env`, `.venv/`, `logs/`,
   `session.json`, `mt_session.json` e `data/limulus.db`.
6. Reiniciar apenas o servico do Limulus e verificar status e logs operacionais.

Uma forma segura de montar o comando de acesso a partir dos campos e:

```text
ssh vps-limulus

# alternativa sem o alias local
ssh -i CAMINHO_DA_CHAVE -p PORTA USUARIO@HOST
```

Nao incluir a chave privada no comando, em logs ou em respostas. O campo
`identidade_ssh` contem somente o caminho local do arquivo.

O alias `vps-limulus` fica no arquivo local `C:\Users\filip\.ssh\config`. Esse
arquivo nao pertence ao repositorio. Ele centraliza o IP, usuario, porta e
caminho da chave para que comandos operacionais nao precisem repetir esses
dados.

## Informacoes Herdadas Do Nautilus

O Nautilus usa `/root/nautilus` e o servico systemd `nautilus-bot`. A
documentacao versionada do Nautilus e propositalmente generica e nao publica IP,
usuario real ou credenciais. Os dois projetos compartilham a VPS, mas cada um
mantem seu proprio diretorio, ambiente virtual, estado e servico.

## Primeiro Preenchimento

Crie `.vps.yml` a partir do modelo:

```powershell
Copy-Item config/vps.exemplo.yml .vps.yml
```

Preencha o host, usuario, porta, caminho da chave, diretorio do Limulus e nome
do servico. Depois disso, futuras IAs devem conseguir localizar o acesso apenas
lendo as instrucoes do repositorio e o arquivo local ignorado.
