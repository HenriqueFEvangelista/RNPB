# RNPB — React & React Native Project Builder

O **RNPB** é um aplicativo desktop em **Python + PySide6** para criar projetos **React Web (Vite)** e **React Native (Expo)** por uma interface gráfica.

> 🚧 **Em desenvolvimento.** As bibliotecas e o EditorManager já foram incorporados à `main` (PRs #9 e #13). O catálogo dinâmico de templates está sendo desenvolvido na issue #14. Gerenciamento de projetos existentes e Expo Tunnel permanecem para entregas futuras.

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

## Descoberta de templates — issue #14

A etapa **Template** mantém as oito opções oficiais locais e permite pesquisar online:

- **Expo:** consulta os diretórios `with-*` do repositório oficial [expo/examples](https://github.com/expo/examples) pela GitHub REST API. Um exemplo aprovado é criado com `npx create-expo-app@latest meu-app --example with-sqlite --yes`. Os exemplos podem definir **JavaScript ou TypeScript por conta própria**, independentemente da linguagem escolhida inicialmente no formulário.
- **React Web/Vite:** consulta repositórios públicos na pesquisa do GitHub para **referência e documentação apenas**. Essas opções são identificadas como comunitárias e **não executáveis** no RNPB, mesmo que tenham "template" no nome; presets Vite oficiais locais continuam sendo os únicos geráveis.
- Mostra origem, descrição, link GitHub e estratégia; a pesquisa usa um worker Qt com **debounce de 650 ms**, timeout e cache em memória de **10 minutos**. Sem conexão, a seleção dos templates oficiais locais permanece acessível ao limpar o filtro de pesquisa.
- URLs, nomes de exemplos e estratégias passam por validação. Resultados externos **não se transformam em comandos shell ou clonagem arbitrária**. Repositórios GitHub não recebem confiança automática.
- Consultas públicas não exigem token nem pagamento; a API do GitHub aplica limites por IP e limites adicionais a pesquisas. Os resultados online não garantem compatibilidade com a versão local do SDK nem funcionamento offline da criação.

**Limitação atual:** não há instalação automática de repositórios comunitários ou busca por templates npm nesta etapa; versões do Expo e dependências do exemplo podem mudar.

## Bibliotecas durante a criação (PR #9)

O assistente apresenta **Projeto → Template → Bibliotecas → Revisão**. Na etapa de bibliotecas o usuário pode não selecionar nada, escolher sugestões locais ou pesquisar pacotes online, filtrando por categoria e, no React Native, pelo indicador de compatibilidade com Expo Go.

**Navegação e validação:** o topo do assistente mostra quatro etapas com ícones e uma barra de progresso. Clique em uma etapa para voltar ou avançar, desde que os campos obrigatórios anteriores estejam corretos. Ao tentar continuar ou criar com nome inválido (por exemplo, usando maiúsculas), sem pasta de destino ou com um projeto já existente, o RNPB abre a etapa correta, destaca o campo e exibe um aviso visível no formulário. O log permanece disponível para diagnósticos de execução.

- Para **React Web**, a busca consulta o **npm Registry** e a instalação adicional usa `npm install nome-do-pacote`.
- Para **React Native**, a busca consulta **npm Registry e React Native Directory** e a instalação adicional usa `npx expo install nome-do-pacote --npm`, respeitando as versões compatíveis conhecidas pelo Expo CLI.
- Dados de compatibilidade Expo Go aparecem como **compatível**, **incompatível** ou **não verificado**. Pacotes que aparecem apenas no npm não são automaticamente considerados compatíveis.
- Consultas HTTP usam workers Qt, timeout e cache **em memória por 10 minutos**. Falhas parciais ou totais são comunicadas; sugestões locais continuam acessíveis.
- O projeto é criado primeiro, depois as dependências-base (Vite) e, por último, as bibliotecas escolhidas. Uma falha na última etapa informa **projeto criado, configuração incompleta**, sem excluir os arquivos.
- O RNPB valida identificadores npm, impede flags/URLs no campo de instalação e permite até **30 pacotes** por criação. Pacotes de terceiros podem executar scripts de instalação e não são auditados automaticamente.

## Abrir projeto em uma IDE (issue #12)

Na página **Editores**, o RNPB detecta Visual Studio Code e Android Studio por PATH,
caminhos convencionais ou Registro do Windows (App Paths). É possível **localizar o executável
manualmente**, remover a configuração e repetir a detecção. O editor selecionado, caminho
manual e opção de abertura automática ficam salvos nas preferências locais do sistema via
`QSettings` (sem alterar os arquivos do projeto).

Após **geração, instalação base e bibliotecas opcionais** concluídas com sucesso,
o RNPB pode abrir a raiz do projeto automaticamente (recurso desativado por padrão).
A página Logs também oferece o botão **Abrir projeto na IDE**. Para Expo sem
diretório nativo `android/`, abre a **raiz do projeto**; não executa prebuild.

- Se nenhum editor for detectado, a criação continua normalmente. Use **Editores → Localizar executável…**.
- O executável deve pertencer ao editor escolhido. Os comandos são invocados com argumentos separados, **sem shell**.
- O Android Studio pode abrir a pasta Expo, mas isso não cria um projeto Android nativo;
  para desenvolvimento Expo Go, o VS Code costuma ser a opção mais direta.
- Falhas ao abrir a IDE são avisos, não cancelam nem invalidam um projeto criado.
- A implementação já foi incorporada à `main` pelo PR #13.

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
- [ADR-0003: catálogo seguro de templates](docs/ADR/0003-catalogo-hibrido-templates.md)
- [APIs e integrações](docs/API.md)
