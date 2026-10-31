# ADR-0001 — Arquitetura modular e geradores oficiais

- **Data:** 31/10/2026
- **Status:** Proposto
- **Escopo:** expansão do RNPB para React web + React Native
- **Autores:** planejamento do projeto RNPB

## Contexto

O RNPB foi iniciado em Python como uma interface desktop para automatizar criação de projetos React Native. No código atual, a GUI usa **CustomTkinter** (`ui/`), as verificações e criação ficam em `core/`, e os comandos são executados via `subprocess`. O caminho Expo/`blank` já existe, mas há limitações de configuração, verificação de sucesso e atualização de UI.

A evolução discutida inclui React web, JavaScript/TypeScript, templates selecionáveis, busca de bibliotecas no npm, verificação de compatibilidade no React Native Directory, templates opcionais via GitHub e execução Expo LAN/Tunnel. Isso exige uma separação mais explícita de responsabilidades.

Também foi avaliado **Python + PySide6 (Qt)** como direção possível para a interface, com **QProcess** para comandos. **A migração não está aprovada nem implementada por este ADR**; PySide6 permanece uma proposta a decidir em separado.

## Decisão proposta

1. **Manter o núcleo em Python** e dividir responsabilidades entre interface, serviços de aplicação, provedores de geradores, provedores de catálogo e executor de processos.
2. **Geradores oficiais como padrão:** Vite para React web e Expo para React Native. Usar templates válidos para cada linguagem/plataforma; não produzir uma combinação inválida artificialmente.
3. **Catálogo híbrido:** manter uma lista local mínima de templates oficiais; consultar npm Registry para pacotes, React Native Directory para metadados de compatibilidade e GitHub apenas para exemplos opcionais. Implementar cache, fallback e política de taxas.
4. **Separar ferramentas de bibliotecas:** por exemplo, `@expo/ngrok` pertence a ferramentas de desenvolvimento, enquanto Axios/Zustand podem integrar dependências de um projeto.
5. **Centralizar execução de processos:** uma interface de executor recebe programa, argumentos, diretório e callbacks de logs/status, e retorna código de saída real; cancelar sem bloquear a interface.
6. **Exigir validação de entradas e origem:** não embutir tokens pessoais nem executar templates externos automaticamente sem revisão/consentimento.

### Desenho lógico pretendido

~~~text
GUI (atual: CustomTkinter; possível: PySide6)
  -> Serviço de criação / validação
     -> Provedor Vite | Provedor Expo
     -> Catálogo local | npm | RN Directory | GitHub (opcional)
     -> Executor de processos + logs, status e cancelamento
~~~

As interfaces internas e nomes de módulos são ilustrativos; esta documentação **não** cria classes, pacotes ou recursos de código.

## Alternativas consideradas

| Alternativa | Benefícios | Custos / motivos para não priorizar |
| --- | --- | --- |
| Permanecer com scripts diretos dentro da GUI | Menos trabalho inicial | Acoplamento cresce com múltiplos geradores e APIs |
| Reescrever desktop em Tauri + React | UI web flexível | Migração completa e necessidade de ferramentas Rust |
| Migrar imediatamente para PySide6 | GUI Qt e QProcess, bom potencial de expansão | Exige reescrita de interface existente; decisão separada |
| Depender exclusivamente de GitHub/templates externos | Catálogo vasto | Rate limits, disponibilidade, manutenção, confiança e segurança |
| Criar gerador próprio de React/React Native | Controle total | Alto custo de manutenção e risco de defasagem |

## Consequências esperadas

**Positivas:** testes isolados por provedor, possibilidade de novas plataformas, interface desacoplada, funcionamento básico mesmo com APIs indisponíveis e operações mais observáveis.

**Desafios:** criação de contratos entre módulos, compatibilidade de versões/SDKs, diferenças entre sistemas operacionais, tratamento de processos longos e curadoria de templates/pacotes.

## Plano de implementação sugerido

1. Primeiro estabilizar criação Expo existente: validar nomes/destinos, sucesso por código de saída, atualização segura da interface, logs e erros reais.
2. Extrair provedores de geração e adicionar React/Vite com seleção JS/TS e templates oficiais.
3. Integrar npm e React Native Directory com cache e indicadores de compatibilidade.
4. Adicionar instalador de bibliotecas e ferramentas opcionais, incluindo o modo Expo Tunnel.
5. Avaliar GitHub para exemplos curados, com autenticação opcional por usuário apenas quando necessária.
6. Registrar ADR específico antes de eventual migração **CustomTkinter → PySide6**.

## Critérios de revisão deste ADR

Revisar quando houver mudança de GUI, gerador, modelo de segurança para repositórios externos, necessidade de autenticação GitHub ou substituição da arquitetura local por um serviço remoto.

## Documentos relacionados

- [Requisitos](../REQUISITOS.md)
- [APIs e integrações](../API.md)
