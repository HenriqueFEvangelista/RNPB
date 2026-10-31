# ADR-0001 — Arquitetura modular e geradores oficiais

- **Data:** 31/10/2026
- **Status:** **Aceito**
- **Escopo:** arquitetura-alvo do RNPB para React web e React Native
- **Decisão:** Python + **PySide6 (Qt Widgets/QSS)**, com **QProcess** para execução de comandos
- **Implementação:** **pendente** — aceitar este ADR não significa que o código tenha sido migrado

## Contexto

O RNPB começou como um aplicativo desktop em **Python + CustomTkinter** para criar projetos React Native via Expo. O repositório hoje mantém UI em `ui/`, código de execução em `core/` e operações por `subprocess`/`threading`. O código ainda não oferece a seleção completa React web/React Native, JS/TS, templates e bibliotecas planejada.

A evolução exigirá interface mais rica, acompanhamento de processos, consultas externas e geradores diversos sem misturar comandos e widgets. A discussão anterior considerou PySide6 e Tauri, mas a tecnologia de interface ainda estava em aberto.

A decisão do projeto em **31/10/2026** encerrou essa escolha: **adotar PySide6** como interface do RNPB e planejar sua migração antes da expansão funcional.

## Decisões aprovadas

1. **GUI:** utilizar **PySide6 / Qt Widgets**, estilos em **QSS**, janela principal com navegação por `QStackedWidget` e widgets reutilizáveis. Não adotar Tauri/React para a GUI desktop.
2. **Linguagem e isolamento:** manter Python e separar `domain` (regras/modelos), `application` (casos de uso/contratos), `infrastructure` (geradores, API, processos, persistência) e `ui` (Qt). O domínio não dependerá do Qt.
3. **CLI:** executar geradores e instalações por **QProcess assíncrono**, com saída em tempo real, código de saída, cancelamento e estados confiáveis. Evitar bloquear a UI ou interpolar entradas do usuário em shell.
4. **HTTP:** integrar APIs com **requests** em workers Qt (`QThreadPool/QRunnable`), com sinais para atualizar a interface e timeouts configurados.
5. **Geradores oficiais:** **Vite para React web** e **Expo para React Native**. O catálogo mínimo contempla React `react`/`react-ts` e Expo `blank`/`blank-typescript`; só disponibilizar templates compatíveis com a linguagem/plataforma escolhida.
6. **Catálogo híbrido:** templates oficiais curados localmente; consulta npm Registry para pacotes e React Native Directory para indicadores de compatibilidade; GitHub API para exemplos adicionais **opcionais, em fase futura**, com cache e respeito a limites.
7. **Instalação:** distinguir bibliotecas do projeto de ferramentas como `@expo/ngrok`; preferir `npx expo install` quando aplicável ao SDK, e oferecer Expo LAN/Tunnel como modos distintos.
8. **Persistência e entrega:** JSON via `platformdirs` para preferências/cache; `pytest`/`pytest-qt` para testes; distribuição inicial Windows com **PyInstaller**. Node.js/npm continuam pré-requisitos externos.
9. **Segurança e confiabilidade:** validar entradas e pastas, evitar sobrescritas, validar saída real do processo, não incluir tokens pessoais no executável, explicitar incompatibilidades e exigir decisão do usuário antes de comandos sensíveis.

Os limites técnicos, estrutura de pastas e fluxos estão especificados em **[ARQUITETURA.md](../ARQUITETURA.md)**, que é parte desta decisão.

## Alternativas analisadas

| Alternativa | Razão para não escolher como padrão |
| --- | --- |
| **CustomTkinter**, tecnologia atual | Menor custo imediato, mas a equipe escolheu o conjunto Qt/Widgets/QProcess para a interface e os processos do produto expandido. |
| **Tauri + React** | Interface flexível, porém requer reescrita em uma stack desktop diferente e ferramentas Rust. |
| **Python + PySide6** | **Escolhida:** preserva Python e fornece componentes Qt, sinais, organização de widgets e QProcess. A migração da UI tem custo inicial. |
| Comandos diretamente na GUI | Acopla fluxos/erros ao widget e dificulta testes e novos geradores. |
| Templates exclusivamente online via GitHub | Rate limits, disponibilidade e riscos de repositórios de terceiros. |
| Geradores React próprios | Manutenção desnecessária diante dos geradores oficiais. |

## Consequências

**Benefícios:** UI mais estruturada; operações externas observáveis; regras testáveis sem GUI; Vite e Expo trocáveis por provedores; pesquisa remota sem bloquear a aplicação; catálogos locais disponíveis quando APIs falham.

**Custos/riscos:** reescrever componentes atuais em PySide6; aprender sinais/slots e QProcess; lidar com scripts `.cmd` no Windows, processos filhos e diferenças entre sistemas; compatibilidade real entre bibliotecas, versões do Expo/SDK e templates; empacotamento Qt via PyInstaller.

**Mitigações:** migrar e estabilizar primeiro o fluxo já existente do Expo; testes por camada, simuladores de processos, validação por etapa; cache e exibição de origem/compatibilidade; sem ações de instalação silenciosas.

## Plano aprovado de implementação

1. Migrar a interface **CustomTkinter → PySide6** e o executor `subprocess` → **QProcess**, mantendo a criação Expo existente durante a transição.
2. Extrair contratos/casos de uso e adicionar Vite, JS/TS e os quatro templates mínimos.
3. Integrar npm Registry/React Native Directory e instalação guiada de bibliotecas, com cache/fallback.
4. Implementar Expo LAN/Tunnel, diagnóstico e abertura de projeto.
5. Adicionar catálogo GitHub de exemplos apenas após validação de segurança, origem e rate limits.

Este ADR **não altera o código** e não declara implementadas as etapas acima. O primeiro PR de código deverá referenciar este documento.

## Reabertura da decisão

Revisar apenas mediante necessidade técnica demonstrável: inviabilidade de Qt/QProcess no ambiente alvo, mudança do modelo de distribuição, exigência de backend próprio ou mudança significativa de geradores/plataformas. Alterações materiais deverão gerar novo ADR, não reescrever silenciosamente o histórico.

## Documentação relacionada

- [Arquitetura técnica](../ARQUITETURA.md)
- [Requisitos](../REQUISITOS.md)
- [APIs e integrações](../API.md)
