# RNPB — React Native Project Builder

O **RNPB** é um aplicativo desktop em **Python + PySide6** para criar e preparar projetos React e React Native por uma interface gráfica, evitando a digitação repetitiva de comandos no terminal.

> 🚧 **Em desenvolvimento.** Esta branch contém a **primeira etapa da migração** de CustomTkinter para PySide6. Atualmente a interface cria apenas projetos **React Native com Expo**, template **blank (JavaScript)**. React web, TypeScript, bibliotecas e Expo Tunnel estão planejados, **não implementados**.

## Recursos da primeira etapa

- Qt Widgets + QSS, navegação para criação e logs.
- Verificação local de Node.js/npm/npx.
- Nome/diretório validados, sem sobrescrever projeto existente.
- Criação Expo `blank` com `npx create-expo-app@latest`.
- Saída do processo em tempo real, sem bloquear a interface, usando `QProcess`.
- Cancelamento de execução, progresso indeterminado e feedback por código de saída.
- O sucesso é conferido também pela existência de `package.json` no destino.

## Executar no Windows

Tenha **Python** e **Node.js** instalados (incluindo npm e npx), e disponíveis no PATH.

~~~powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
~~~

Para executar os testes:

~~~powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
~~~

Para distribuir um executável Windows, instale os requisitos de desenvolvimento e depois execute:

~~~powershell
pyinstaller RNPB.spec
~~~

O empacotamento não instala Node.js/npm no computador do usuário.

## Avisos

- A criação pelo npm/Expo normalmente requer conexão com a internet.
- Cancelar um processo pode deixar arquivos parcialmente criados; **o RNPB não os apaga automaticamente**.
- A interrupção de processos filhos iniciados pelos geradores pode variar por sistema operacional e requer testes adicionais em Windows.
- A pesquisa de bibliotecas e os demais templates ainda não foram implementados.

## Documentação

- [Documentação inicial](docs/README.md)
- [Arquitetura planejada](docs/ARQUITETURA.md)
- [Requisitos](docs/REQUISITOS.md)
- [ADR-0001](docs/ADR/0001-arquitetura-e-geradores.md)
- [APIs e integrações](docs/API.md)
