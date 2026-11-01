# Requisitos do RNPB

**Versão:** levantamento inicial (31/10/2026)  
**Situação:** acompanhamento de requisitos e implementação; funcionalidades marcadas como PR só entram na `main` após merge.

## 1. Visão do produto

O RNPB simplifica a criação e a preparação de projetos **React (web)** e **React Native (mobile)** por meio de uma interface gráfica desktop. O usuário deverá informar nome e destino do projeto, escolher plataforma, linguagem e template, selecionar bibliotecas opcionais e acompanhar a execução sem precisar digitar os comandos manualmente.

Público-alvo: estudantes, iniciantes e desenvolvedores que desejam automatizar configurações recorrentes.

## 2. Estado atual e evolução

A arquitetura **Python + PySide6 (Qt Widgets/QSS) + QProcess** foi aprovada no [ADR-0001](./ADR/0001-arquitetura-e-geradores.md). O PR #4 migrou a interface e a execução do Expo, incorporado à `main`; o PR #7 implementou React Web (Vite), JS/TS e templates oficiais e já foi incorporado à `main`. O PR #9 implementa a seleção e instalação opcional de bibliotecas durante a criação e ainda está em revisão.

As regras de templates, catálogo de pacotes, integração HTTP e planos de instalação ficam em `core/`; `ui/` apresenta o wizard, executa as buscas em workers Qt e orquestra geração e instalação. A organização modular completa de [ARQUITETURA.md](./ARQUITETURA.md) permanece uma evolução incremental.

## 3. Requisitos funcionais

| ID | Requisito | Prioridade | Situação |
| --- | --- | --- | --- |
| RF-01 | Selecionar React web ou React Native na criação. | Alta | Implementado no PR #7 |
| RF-02 | Selecionar JavaScript ou TypeScript, conforme as opções do gerador. | Alta | Implementado no PR #7 |
| RF-03 | Selecionar templates oficiais válidos para a plataforma/linguagem. | Alta | Implementado no PR #7 |
| RF-04 | Definir nome e pasta, validar entradas e evitar sobrescrever projetos existentes. | Alta | Parcial |
| RF-05 | Identificar Node.js, npm/npx e informar erros de pré-requisitos. | Alta | Parcial |
| RF-06 | Criar React web com gerador oficial Vite. | Alta | Implementado no PR #7, pendente teste manual |
| RF-07 | Criar React Native com gerador oficial Expo. | Alta | Implementado; opções TS no PR #7 |
| RF-08 | Pesquisar pacotes no npm Registry e mostrar metadados relevantes. | Alta | Implementado no PR #9 |
| RF-09 | Filtrar bibliotecas React Native por plataforma e indicação de compatibilidade com Expo Go. | Média | Parcial no PR #9: filtro Expo Go; filtros individuais Android/iOS ainda não implementados |
| RF-10 | Selecionar bibliotecas e ferramentas opcionais, instalar com o gerenciador apropriado e apresentar o resultado individual. | Alta | Parcial no PR #9: instalação de pacotes na criação e resultado da etapa; ferramentas e gerenciamento posterior pendentes |
| RF-11 | Executar Expo em modo LAN ou Tunnel (`@expo/ngrok` opcional), exibindo instruções/QR Code quando disponível. | Média | Planejado |
| RF-12 | Exibir logs em tempo real, status, falhas reais, resultado e permitir cancelamento seguro. | Alta | Parcial |
| RF-13 | Abrir o diretório resultante e, opcionalmente, o projeto no VS Code. | Média | Planejado |
| RF-14 | Disponibilizar catálogo local e cache para o funcionamento básico quando APIs estiverem indisponíveis. | Alta | Planejado |
| RF-15 | Consultar exemplos/templates de terceiros via GitHub, com origem, licença e riscos explicitados. | Baixa | Futuro |

**Observações de compatibilidade:** os templates oficiais do Expo têm combinações próprias de linguagem; nem todo template está disponível em JavaScript. Pacotes React web não devem ser apresentados automaticamente como compatíveis com React Native. Os dados externos são indicativos e precisam de validação.

## 4. Critérios de aceitação do MVP proposto

- Dado um destino vazio, nome válido, **React + JavaScript**, gerar o projeto Vite usando o template correto.
- Dado **React + TypeScript**, gerar o template React TS sem alterar arquivos manualmente.
- Dado **React Native + JavaScript**, oferecer template Expo compatível (por exemplo, `blank`); dado **TypeScript**, oferecer `blank-typescript` ou outro template compatível.
- Não habilitar combinações incompatíveis de plataforma, template e linguagem.
- Dado Node.js/npm/npx indisponível, bloquear a criação e indicar de forma compreensível como corrigir o ambiente.
- Mostrar a saída do processo e considerar sucesso **somente após código de saída 0**; falhas não devem exibir a mensagem de sucesso.
- Permitir selecionar uma ou mais bibliotecas, mostrando origem e compatibilidade antes da instalação; para projetos Expo, preferir `npx expo install` quando aplicável.
- Sem acesso à rede ou com API indisponível, manter templates oficiais em catálogo local; comunicar claramente as funções que requerem conexão.

## 5. Requisitos não funcionais

| ID | Requisito |
| --- | --- |
| RNF-01 | A interface PySide6 não deve travar durante instalações ou buscas; QProcess será usado para comandos e workers Qt para HTTP. |
| RNF-02 | Estados de progresso devem ser fiéis: usar etapas/indeterminação quando a duração não puder ser medida. |
| RNF-03 | Processos devem ter timeout quando apropriado, captura de erros, logs e cancelamento seguro. |
| RNF-04 | Não interpolar entradas do usuário em comandos shell; validar nomes e caminhos e respeitar permissões locais. |
| RNF-05 | Não embutir tokens pessoais do GitHub nem segredos em executáveis ou código-fonte. |
| RNF-06 | Usar cache e limites de requisição; falhas de serviços externos não devem impedir o uso de geradores oficiais. |
| RNF-07 | O MVP será testado prioritariamente no Windows; suporte multiplataforma exige validação específica. |
| RNF-08 | O executável desktop poderá ser distribuído com PyInstaller sem exigir Python instalado; **Node.js e npm** continuam como pré-requisitos para gerar projetos. |
| RNF-09 | Interface legível, com feedback claro, textos acessíveis e navegação por teclado quando viável. |
| RNF-10 | Implementar testes com pytest e pytest-qt para regras de criação, validação, APIs, sinais da interface e estados de execução. |

## 6. Roadmap de entrega (proposta)

**Fase 1 — Migração e núcleo confiável:** PySide6/QProcess (PR #4) e React Web/Vite com JS/TS/templates (PR #7) foram incorporados à `main` e validados manualmente pelo mantenedor. Continuam necessárias verificações de cancelamento real, compatibilidade de versões Node e empacotamento.

**Fase 2 — Catálogo e configuração:** PR #9 implementa busca npm Registry + React Native Directory, catálogo local, filtros básicos e instalação opcional durante a criação, com cache em memória. Página de projetos existentes, cache persistente e filtros adicionais seguem pendentes.

**Fase 3 — Experiência de desenvolvimento:** alternar Expo LAN/Tunnel, verificar/instalar `@expo/ngrok` com consentimento, abrir projeto no editor e melhorar diagnóstico.

**Fase 4 — Expansões:** GitHub para templates adicionais previamente avaliados, gerenciamento de projetos existentes, novos gerenciadores de pacotes, histórico e templates personalizados.

## 7. Fora do escopo inicial

- Executar um backend próprio de catálogo/API.
- Substituir npm, Vite ou Expo por geradores próprios.
- Garantir compatibilidade de toda biblioteca ou template de terceiros.
- Incluir credenciais compartilhadas de serviços externos no aplicativo.

## 8. Pendências de decisão

- A escolha **PySide6** está encerrada e a migração inicial foi incorporada no PR #4; futuras melhorias seguem a arquitetura adotada.
- Nome final do produto após incluir React web.
- O catálogo inicial de sugestões consta no PR #9 e deverá ser revisado conforme compatibilidade e necessidade.
- Estratégia de distribuição/atualização do executável.

Ver também [ARQUITETURA.md](./ARQUITETURA.md), [API.md](./API.md) e [ADR-0001](./ADR/0001-arquitetura-e-geradores.md).
