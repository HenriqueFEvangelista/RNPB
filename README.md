# RNPB — React & React Native Project Builder

O **RNPB** é um aplicativo desktop em **Python + PySide6** para criar projetos **React Web (Vite)** e **React Native (Expo)** por uma interface gráfica.

> 🚧 **Em desenvolvimento.** Nesta etapa, já é possível selecionar plataforma, JavaScript/TypeScript e templates oficiais. Pesquisa e instalação de bibliotecas opcionais, Expo Tunnel e gerenciamento de projetos existentes ficam para etapas futuras.

## Recursos disponíveis

- Interface Qt Widgets + QSS, navegação e logs de execução.
- Seleção de **React Web · Vite** ou **React Native · Expo**, JavaScript ou TypeScript.
- Templates compatíveis com cada opção, mantidos em catálogo local:
  - **Vite/JS:** `react`, `react-compiler`;
  - **Vite/TS:** `react-ts`, `react-compiler-ts`;
  - **Expo/JS:** `blank`;
  - **Expo/TS:** `blank-typescript`, `default`, `tabs`.
- Para React Web: geração do scaffold Vite **seguida de `npm install`**.
- Para React Native: geração pelo `create-expo-app`, que já prepara as dependências.
- Validação de nome/diretório sem sobrescrever projeto, detecção de Node.js/npm/npx.
- Processos assíncronos com `QProcess`, logs em tempo real, cancelamento e tratamento de falhas.
- O sucesso depende do código de saída e da presença de `package.json`; para Vite, valida a instalação de `node_modules`.

## Executar no Windows

Pré-requisitos: **Python e Node.js (npm/npx)** instalados no PATH. A versão atual do Vite requer **Node.js 20.19+ ou 22.12+**; alguns templates podem exigir versões superiores. O aplicativo verifica a presença do Node.js, mas ainda não compara sua versão.

~~~powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
~~~

Executar testes:

~~~powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
~~~

Para gerar o executável Windows (validação final ainda pendente):

~~~powershell
pyinstaller RNPB.spec
~~~

O empacotamento não inclui Node.js/npm.

## Observações

- Criar projetos normalmente requer internet para baixar pacotes e dependências.
- O Expo tem disponibilidade de SDKs e compatibilidade de Expo Go que podem variar; `default` e `tabs` usam TypeScript.
- Cancelar pode deixar arquivos parciais. O RNPB não os apaga automaticamente.
- Um Vite gerado sem `npm install` não está pronto para uso; o RNPB faz essa etapa automaticamente.
- Testes de cancelamento real, compatibilidade com diferentes versões do Node e empacotamento permanecem necessários.

## Documentação

- [Documentação](docs/README.md)
- [Arquitetura](docs/ARQUITETURA.md)
- [Requisitos](docs/REQUISITOS.md)
- [ADR-0001](docs/ADR/0001-arquitetura-e-geradores.md)
- [APIs e integrações](docs/API.md)
