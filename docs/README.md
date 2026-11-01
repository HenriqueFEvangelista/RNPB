# Documentação do RNPB

> Documentação inicial de planejamento — 31/10/2026.

O **RNPB (React Native Project Builder)** nasceu como um aplicativo desktop em Python para criar projetos React Native por uma interface gráfica, sem exigir que o usuário digite os comandos de preparação no terminal. A evolução proposta amplia o alcance para **React (web) e React Native (mobile)**. O nome definitivo do produto após essa ampliação ainda está em aberto.

## Índice

- [Requisitos](./REQUISITOS.md) — escopo, requisitos funcionais e não funcionais, critérios de aceitação e roadmap.
- [Arquitetura técnica](./ARQUITETURA.md) — módulos, contratos, fluxos, estados e plano de migração.
- [Documentação de APIs e integrações](./API.md) — npm Registry, React Native Directory, GitHub e ferramentas locais.
- [ADR-0001: arquitetura e estratégia de geração](./ADR/0001-arquitetura-e-geradores.md) — decisão **aceita**, contexto, alternativas e consequências.

## Estado da implementação (PR #7)

**Implementado no código da branch `feat/react-vite-js-ts-templates` (pendente de merge):**
- Aplicativo desktop em **Python + PySide6 / Qt Widgets / QSS** e execução assíncrona com **QProcess**.
- Módulos atuais em `ui/` e `core/`; a organização completa da arquitetura-alvo ainda é evolutiva.
- Geradores **React Web (Vite)** e **React Native (Expo)**, seleção de JavaScript/TypeScript e catálogo local de templates oficiais.
- Criação Vite seguida de **`npm install`** no projeto gerado; Expo usa `create-expo-app`.
- Validação de ambiente, destino, combinação de template, logs e status de erro/cancelamento.
- Testes unitários e Qt via GitHub Actions no Windows e Linux.

**Planejado para próximas etapas:**
- Pesquisa e instalação opcional de bibliotecas, filtros de compatibilidade e cache.
- Integração com npm Registry, React Native Directory e GitHub (este último opcional).
- Expo LAN/Tunnel, abertura no editor e gerenciamento de projetos existentes.
- Validação manual dos novos geradores em Windows e empacotamento final com PyInstaller.

A presença de um requisito ou de uma integração nestes arquivos **não indica que a funcionalidade já esteja disponível**.

## Princípios

1. Priorizar geradores **oficiais e conhecidos**: Vite para React web e Expo para React Native.
2. Fazer a criação essencial funcionar sem depender das APIs de catálogo.
3. Exibir comandos, logs e falhas de forma transparente.
4. Evitar segredos embutidos no executável e tratar templates/pacotes externos como fontes não confiáveis.
5. Separar interface, regras de negócio, integrações externas e execução de processos para facilitar manutenção.

A arquitetura-base foi aprovada em 31/10/2026. A implementação deverá ser acompanhada de atualizações nesta documentação conforme os recursos forem entregues.
