# Documentação do RNPB

> Documentação inicial de planejamento — 31/10/2026.

O **RNPB (React Native Project Builder)** nasceu como um aplicativo desktop em Python para criar projetos React Native por uma interface gráfica, sem exigir que o usuário digite os comandos de preparação no terminal. A evolução proposta amplia o alcance para **React (web) e React Native (mobile)**. O nome definitivo do produto após essa ampliação ainda está em aberto.

## Índice

- [Requisitos](./REQUISITOS.md) — escopo, requisitos funcionais e não funcionais, critérios de aceitação e roadmap.
- [Arquitetura técnica](./ARQUITETURA.md) — módulos, contratos, fluxos, estados e plano de migração.
- [Documentação de APIs e integrações](./API.md) — npm Registry, React Native Directory, GitHub e ferramentas locais.
- [ADR-0001: arquitetura e estratégia de geração](./ADR/0001-arquitetura-e-geradores.md) — decisão **aceita**, contexto, alternativas e consequências.

## Estado da implementação (PR #9)

**Implementado e integrado à `main`:** PySide6/QProcess (PR #4); React Web/Vite, Expo, JS/TS e templates oficiais (PR #7).

**Na branch do PR #9, ainda em revisão:**
- Assistente com etapas **Projeto → Template → Bibliotecas → Revisão**.
- Catálogo local de sugestões + busca npm Registry e React Native Directory.
- Workers Qt, debounce, timeout, cache em memória e fallback em caso de API indisponível.
- Instalação opcional após criação com `npm install` ou `npx expo install`; validação de saída e do `package.json`.
- Indicadores de compatibilidade Expo Go que distinguem confirmado, incompatível e não verificado.
- Testes unitários e de interface para consultas, instalação e falha parcial.

**Ainda planejado:** página de projetos existentes, cache persistente, GitHub API para templates externos, Expo Tunnel, atualização/remoção de pacotes e verificação final do executável no Windows.

## Princípios

1. Priorizar geradores **oficiais e conhecidos**: Vite para React web e Expo para React Native.
2. Fazer a criação essencial funcionar sem depender das APIs de catálogo.
3. Exibir comandos, logs e falhas de forma transparente.
4. Evitar segredos embutidos no executável e tratar templates/pacotes externos como fontes não confiáveis.
5. Separar interface, regras de negócio, integrações externas e execução de processos para facilitar manutenção.

A arquitetura-base foi aprovada em 31/10/2026. A implementação deverá ser acompanhada de atualizações nesta documentação conforme os recursos forem entregues.
