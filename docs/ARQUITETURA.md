# Arquitetura técnica do RNPB

- **Data da decisão:** 31/10/2026
- **Status:** arquitetura-alvo **aprovada**; PRs #4 e #7 incorporados e catálogo/instalação do PR #9 em revisão.
- **Decisão relacionada:** [ADR-0001](./ADR/0001-arquitetura-e-geradores.md)
- **Escopo:** aplicativo desktop para criar projetos React web e React Native

## 1. Objetivos e fronteiras

O RNPB permitirá escolher **plataforma, JavaScript/TypeScript, template, destino e bibliotecas** por interface gráfica, executando geradores e instaladores oficiais. O aplicativo não substitui Vite, Expo ou npm e não precisa de servidor próprio no MVP.

**Estado do repositório:** o PR #4 incorporou **Python + PySide6/QProcess** na `main`. O PR #7 adicionou Vite/Expo com JS/TS e templates por catálogo local. O PR #9 acrescenta a seleção opcional de bibliotecas durante a criação, via catálogo local, npm Registry e React Native Directory. A árvore de módulos a seguir é uma **estrutura-alvo**, ainda não corresponde literalmente aos caminhos atuais em `ui/` e `core/`.

## 2. Stack definida

| Responsabilidade | Escolha |
| --- | --- |
| Linguagem e lógica | Python |
| Desktop GUI | **PySide6 / Qt Widgets**, entrada via `QApplication` e janela principal `QMainWindow` |
| Estilos e recursos | **QSS**, ícones SVG e recursos Qt; separar tema dos componentes |
| Navegação e páginas | `QStackedWidget` com páginas/widgets de responsabilidade única |
| Execução de comandos externos | **QProcess** assíncrono; sinais de saída, erro, conclusão e cancelamento |
| Consultas HTTP | **requests** com timeout em workers `QThreadPool/QRunnable`; atualizar GUI apenas via sinais Qt |
| Geradores oficiais | **Vite** (React web) e **Expo** (React Native) |
| Metadados de pacotes | npm Registry; React Native Directory para indicadores de compatibilidade |
| Exemplos/templates de terceiros | GitHub REST API **opcional e posterior**, com curadoria e cache |
| Configurações e cache | JSON em diretórios de usuário via `platformdirs`; catálogo curado embarcado |
| Testes | `pytest`, `pytest-qt`, objetos falsos para APIs/processos |
| Executável Windows | PyInstaller; Node.js/npm instalados e acessíveis externamente |

Não adotaremos Tauri/React para a própria interface, nem criaremos um backend remoto para este MVP.

## 3. Organização de código alvo (proposta adotada)

~~~text
RNPB/
├── main.py                       # entrada mínima
├── rnpb/
│   ├── bootstrap.py              # configura QApplication e dependências
│   ├── domain/
│   │   ├── models.py             # ProjectSpec, PackageSpec, CommandSpec
│   │   └── validation.py         # regras puras de validação
│   ├── application/
│   │   ├── create_project.py     # orquestra o fluxo de criação
│   │   ├── install_packages.py   # orquestra dependências
│   │   ├── run_project.py        # controla execução Expo LAN/Tunnel
│   │   └── ports.py              # contratos independentes da UI
│   ├── infrastructure/
│   │   ├── generators/
│   │   │   ├── vite.py
│   │   │   └── expo.py
│   │   ├── catalogs/
│   │   │   ├── curated.py        # templates oficiais locais
│   │   │   ├── npm.py
│   │   │   ├── react_native_directory.py
│   │   │   └── github.py        # somente em fase posterior
│   │   ├── process/
│   │   │   └── qt_process_runner.py
│   │   └── persistence/
│   │       ├── settings.py
│   │       └── cache.py
│   └── ui/
│       ├── main_window.py
│       ├── pages/
│       │   ├── create_project.py
│       │   ├── packages.py
│       │   └── run_project.py
│       └── widgets/
│           └── logs_panel.py
├── resources/                    # QSS, SVG e catálogos embarcados
├── tests/
└── docs/
~~~

O layout é **arquitetura-alvo** para orientar os commits da migração, não descrição do diretório atual. Evitar camadas ou arquivos vazios sem uma necessidade real.

## 4. Regras de dependência

~~~text
UI (PySide6/Qt)
    ↓ solicita operações, recebe sinais
Application (casos de uso + portas/contratos)
    ↓ regras puras
Domain (modelos e validação, sem Qt ou rede)

Infrastructure (adaptadores concretos: QProcess, npm, Expo, Vite, HTTP, JSON)
    → implementa as portas usadas por Application
~~~

- **Domain:** não importa PySide6, requests nem frameworks de UI. Modelos imutáveis e funções de validação quando aplicável.
- **Application:** conhece `ProjectSpec` e contratos como `ProjectGenerator`, `PackageCatalog` e `ProcessRunner`, sem executar comandos diretamente.
- **Infrastructure:** traduz planos em comandos, consulta APIs e persiste cache. A infraestrutura Qt é injetada na aplicação pelo bootstrap.
- **UI:** valida feedback de formulário, apresenta seleção e logs, mas não monta comandos nem chama npm diretamente.

Uma camada só pode depender de contratos mais internos; integrações concretas são montadas na inicialização.

## 5. Contratos de domínio e fluxos

### 5.1 Modelos propostos

- `ProjectSpec`: `name`, `target` (`react-web`/`react-native`), `language` (`javascript`/`typescript`), `template_id`, `destination`, `packages`.
- `TemplateSpec`: ID estável, origem, gerador, plataformas e linguagens suportadas.
- `PackageSpec`: nome, versão/metadados conhecidos, origem, suporte informado, modo de instalação e indicação `expo_go` (`compatible`/`incompatible`/`unknown`).
- `CommandSpec`: executável, lista de argumentos, diretório de trabalho e ajustes de ambiente permitidos.
- `ExecutionResult`: código de saída, estado (`success`/`failed`/`cancelled`), mensagem e referências de log.

O formato será refinado em código/testes, mantendo regras independentes da GUI.

### 5.2 Pipeline de criação

1. **Validar:** nome, caminho, permissões, destino, plataforma/linguagem/template e sobrescrita.
2. **Verificar ambiente:** Node.js, npm/npx, versões compatíveis e conectividade quando necessária.
3. **Resolver plano:** selecionar provedor Vite/Expo e template aprovado do catálogo local.
4. **Gerar:** iniciar processo por `QProcess`, capturar saída e código de retorno.
5. **Instalar extras (opcional):** processar bibliotecas selecionadas com estratégias npm ou Expo compatíveis.
6. **Verificar:** código de saída, existência dos artefatos esperados e sucesso de cada instalação.
7. **Concluir:** informar caminho, falhas/avisos, opção de abrir pasta/VS Code; nunca anunciar êxito antes de verificar.

**Estados:** `idle → validating → checking_environment → generating → installing? → verifying → success`; em qualquer operação apropriada, `failed` ou `cancelled`. Emitir progresso por etapas; usar indicador indeterminado enquanto não houver progresso mensurável.

Não remover automaticamente diretórios existentes. Em falha com projeto parcialmente criado, preservar os arquivos e explicar como proceder; uma eventual limpeza requer consentimento explícito.

### 5.3 Geradores oficiais e pacotes

| Tipo | Idioma | Template inicial | Gerador |
| --- | --- | --- | --- |
| React Web | JavaScript | `react` | Vite |
| React Web | TypeScript | `react-ts` | Vite |
| React Native | JavaScript | `blank` | Expo |
| React Native | TypeScript | `blank-typescript` | Expo |

Esses são os **quatro fluxos mínimos aceitos**. O PR #7 também inclui `react-compiler`, `react-compiler-ts` (Vite) e `default`/`tabs` (Expo, TypeScript). A lista é curada localmente; novas opções exigem validação por plataforma/linguagem/versão. O gerador Vite exige uma segunda etapa `npm install` no diretório gerado.

- React web: criar por `npm create vite@latest ...`; instalar extras por npm.
- Expo: criar por `npx create-expo-app@latest ...`; preferir `npx expo install` para pacotes gerenciados pelo SDK.
- Não usar o legado `npx react-native init` no novo fluxo padrão.
- Diferenciar **dependências do projeto** de **ferramentas de desenvolvimento**, como `@expo/ngrok`, que podem requerer instalação opcional separada.

## 6. Execução e concorrência

### CLI via QProcess

- `QProcess` será criado e controlado no thread Qt da aplicação, com API **assíncrona orientada a sinais**, sem `waitForFinished()` bloqueante na GUI.
- Adaptador único por plataforma localiza `node`, `npm`/`npm.cmd` e `npx`/`npx.cmd`. Evitar shell genérico, interpolação de texto de usuário ou comandos concatenados; lidar com particularidades de `.cmd` no Windows num adaptador testado.
- Conectar sinais de stdout, stderr, término e erro; construir `ExecutionResult` considerando código de saída e estado de término.
- O botão cancelar solicitará interrupção e, se necessário, encerramento controlado; documentar e testar processo/filhos remanescentes por SO.
- Cada job de criação tem executor/estado próprios. Impedir início duplicado e controlar a sequência geração → instalação.

### Rede via workers Qt

- Consultas HTTP com `requests` em `QThreadPool`/`QRunnable` e timeout explícito.
- A UI recebe resultado/erro por **signals/slots**; workers nunca alteram widgets diretamente.
- Descartar resultados obsoletos quando pesquisa muda; limitar concorrência e usar cache.
- Evitar execução simultânea de operações conflitantes no mesmo diretório de projeto.

## 7. Integrações, fallback e segurança

- **Templates oficiais locais:** a criação fundamental não depende de chamadas à GitHub API ou ao React Native Directory; a geração em si requer as ferramentas/dependências necessárias e, normalmente, internet na primeira criação.
- **npm Registry:** busca sob demanda, resultados paginados/limitados e metadados não confiáveis por padrão.
- **React Native Directory:** indicadores de compatibilidade com Android/iOS/web/Expo Go; ausência de informação significa `unknown`, não compatível.
- **GitHub:** catálogo adicional **fora do núcleo do MVP**; consultas públicas sem token quando possível, cache/rate limit; não embarcar token compartilhado.
- **Expo Tunnel:** selecionar LAN/Tunnel na execução do projeto; oferecer instalação voluntária de `@expo/ngrok` e explicar dependência da internet e políticas da rede.
- **Cache e configurações:** JSON no espaço do usuário via `platformdirs`; cache com data da consulta, origem, validade e degradação explícita quando desatualizado. Nunca escrever arquivos de configuração dentro do diretório de instalação do executável.
- **Segurança:** validar nomes/caminhos/pacotes, apresentar comandos antes de executar ações relevantes, não executar automaticamente templates de terceiros, expor risco de scripts de instalação e não registrar segredos nos logs.

## 8. Testes, qualidade e distribuição

**Testes unitários:** validação dos modelos, seleção de template, construção de `CommandSpec`, seleção npm/Expo, cache e normalização de respostas de APIs (fixtures).

**Testes de integração:** executor Qt com processo de teste inofensivo, sinais e encerramento; fluxos simulados com `ProcessRunner` falso, incluindo erros/cancelamento.

**Testes de UI:** `pytest-qt` para estados, navegação, mensagens de log e não bloqueio de operações.

**Testes manuais Windows:** Node ausente, nome inválido, destino existente, React JS/TS, Expo JS/TS, interrupção, falha de rede, API fora do ar, Expo LAN/Tunnel em redes distintas.

**Distribuição:** PyInstaller inclui Python e Qt necessários à GUI; **não inclui automaticamente Node.js/npm**. Detectar e explicar pré-requisitos. Windows será a plataforma prioritária do MVP.

## 9. Sequência de implementação aprovada

1. **Migração do shell desktop:** PySide6/Qt Widgets/QSS, navegação, logs, verificação de ambiente e runner QProcess. Reproduzir o fluxo Expo existente, corrigindo sucessos incorretos/atualizações inseguras da GUI.
2. **Geradores e linguagens:** separar domínio, casos de uso e provedores; implementar quatro combinações mínimas Vite/Expo com JS/TS.
3. **Catálogo e instalação:** npm + React Native Directory em workers, cache, seleção e instalação por estratégia.
4. **Ferramentas de execução:** Expo LAN/Tunnel, diagnóstico e abertura de projeto.
5. **Evolução opcional:** GitHub para exemplos curados, histórico de projetos, pnpm/Yarn, novos frameworks.

### Limites e decisões que não impedem começar

O nome **RNPB** permanece como nome do repositório/produto nesta fase; eventual renomeação comercial é independente da arquitetura. Versões mínimas exatas de Python/PySide6/Node, política de atualização do binário e conjunto de bibliotecas curadas serão fixados durante setup/testes de compatibilidade, sem alterar estas decisões de alto nível.

## 10. Rastreamento

- [ADR-0001 — decisão aceita](./ADR/0001-arquitetura-e-geradores.md)
- [Requisitos](./REQUISITOS.md)
- [APIs e integrações](./API.md)

## 11. Catálogo e instalador — implementação incremental (PR #9)

Antes da reorganização integral em `rnpb/`, a primeira versão foi implementada nos diretórios existentes:

- `core/packages.py`: modelos, sugestões locais e validação de identificadores npm.
- `core/package_catalog.py`: acesso a npm Registry/React Native Directory e cache em memória de 600 segundos.
- `core/package_installer.py`: comandos de instalação e verificação do manifest.
- `ui/package_selector.py`: pesquisa, categorias, filtro Expo Go e seleção múltipla.
- `ui/catalog_worker.py`: HTTP assíncrono em workers Qt, com timeout e sinais.
- `ui/create_view.py`: wizard com 4 etapas; `ui/app.py`: pipeline de geração, dependências-base e instalação opcional.

**Regra de compatibilidade:** sem metadados positivos explícitos do Directory, o resultado Expo Go é `unknown` (não verificado). A compatibilidade por SDK não é garantida. O usuário escolhe pacotes voluntariamente após revisão; scripts npm podem ser executados pelo gerenciador de pacotes.

**Falha parcial:** o projeto permanece no disco e a UI informa que bibliotecas opcionais não foram instaladas. Resultados de pesquisas externas são tratados como dados não confiáveis. Não há tokens compartilhados embutidos no aplicativo.

A futura página de projetos existentes reutilizará o seletor, mas não faz parte deste PR.
