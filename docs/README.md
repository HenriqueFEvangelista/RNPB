# Documentação do RNPB

> Documentação inicial de planejamento — 31/10/2026.

O **RNPB (React Native Project Builder)** nasceu como um aplicativo desktop em Python para criar projetos React Native por uma interface gráfica, sem exigir que o usuário digite os comandos de preparação no terminal. A evolução proposta amplia o alcance para **React (web) e React Native (mobile)**. O nome definitivo do produto após essa ampliação ainda está em aberto.

## Índice

- [Requisitos](./REQUISITOS.md) — escopo, requisitos funcionais e não funcionais, critérios de aceitação e roadmap.
- [Arquitetura técnica](./ARQUITETURA.md) — módulos, contratos, fluxos, estados e plano de migração.
- [Documentação de APIs e integrações](./API.md) — npm Registry, React Native Directory, GitHub e ferramentas locais.
- [ADR-0001: arquitetura e estratégia de geração](./ADR/0001-arquitetura-e-geradores.md) — decisão **aceita**, contexto, alternativas e consequências.

## Estado do repositório na criação destes documentos

**Implementado / presente no código:**
- Aplicativo desktop em **Python + CustomTkinter** (não em PySide6).
- Módulos em `ui/` e `core/`.
- Fluxo de criação de projeto Expo com template `blank` via `npx create-expo-app@latest`.
- Verificações de ambiente (Node.js e npm), visualização de logs e indicador de progresso por etapas.
- Execução de comandos via `subprocess` e thread de trabalho.

**Planejado, não implementado nesta documentação:**
- React web com Vite; seleção de JavaScript/TypeScript e templates.
- Catálogo de bibliotecas, filtros de compatibilidade e instalação pela interface.
- Integração com npm Registry, React Native Directory e GitHub.
- Execução do Expo Go nos modos LAN/Tunnel; melhorias de cancelamento, tratamento de erros e gerenciamento de projetos.
- Migração **aprovada** da interface para **PySide6 + Qt Widgets/QSS**, com `QProcess` no lugar da execução atual; a migração **ainda não foi codificada**.

A presença de um requisito ou de uma integração nestes arquivos **não indica que a funcionalidade já esteja disponível**.

## Princípios

1. Priorizar geradores **oficiais e conhecidos**: Vite para React web e Expo para React Native.
2. Fazer a criação essencial funcionar sem depender das APIs de catálogo.
3. Exibir comandos, logs e falhas de forma transparente.
4. Evitar segredos embutidos no executável e tratar templates/pacotes externos como fontes não confiáveis.
5. Separar interface, regras de negócio, integrações externas e execução de processos para facilitar manutenção.

A arquitetura-base foi aprovada em 31/10/2026. A implementação deverá ser acompanhada de atualizações nesta documentação conforme os recursos forem entregues.
