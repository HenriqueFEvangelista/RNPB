# RNPB — React & React Native Project Builder

O **RNPB** é um aplicativo desktop em **Python + PySide6** para criar projetos **React Web (Vite)** e **React Native (Expo)** por uma interface gráfica.

> 🚧 **Em desenvolvimento.** O PR #9 acrescenta um assistente com quatro etapas e seleção opcional de bibliotecas durante a criação. O gerenciamento de pacotes em projetos existentes, Expo Tunnel e atualização/remoção de bibliotecas permanecem para entregas futuras.

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

## Bibliotecas durante a criação (PR #9)

O assistente apresenta **Projeto → Template → Bibliotecas → Revisão**. Na etapa de bibliotecas o usuário pode não selecionar nada, escolher sugestões locais ou pesquisar pacotes online, filtrando por categoria e, no React Native, pelo indicador de compatibilidade com Expo Go.

- Para **React Web**, a busca consulta o **npm Registry** e a instalação adicional usa `npm install nome-do-pacote`.
- Para **React Native**, a busca consulta **npm Registry e React Native Directory** e a instalação adicional usa `npx expo install nome-do-pacote --npm`, respeitando as versões compatíveis conhecidas pelo Expo CLI.
- Dados de compatibilidade Expo Go aparecem como **compatível**, **incompatível** ou **não verificado**. Pacotes que aparecem apenas no npm não são automaticamente considerados compatíveis.
- Consultas HTTP usam workers Qt, timeout e cache **em memória por 10 minutos**. Falhas parciais ou totais são comunicadas; sugestões locais continuam acessíveis.
- O projeto é criado primeiro, depois as dependências-base (Vite) e, por último, as bibliotecas escolhidas. Uma falha na última etapa informa **projeto criado, configuração incompleta**, sem excluir os arquivos.
- O RNPB valida identificadores npm, impede flags/URLs no campo de instalação e permite até **30 pacotes** por criação. Pacotes de terceiros podem executar scripts de instalação e não são auditados automaticamente.

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
