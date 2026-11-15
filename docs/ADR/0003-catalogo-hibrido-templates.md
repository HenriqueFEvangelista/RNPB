# ADR-0003 — Catálogo híbrido e descoberta segura de templates

- **Data:** 15/11/2026
- **Status:** aceito para implementação na issue #14
- **Relacionados:** [ADR-0001](./0001-arquitetura-e-geradores.md), [ADR-0002](./0002-abertura-de-editores.md)

## Contexto

Os templates iniciais do RNPB eram oito opções codificadas diretamente em
`core/templates.py`. A instalação de bibliotecas por npm/React Native Directory
já foi incorporada no PR #9, mas não fornece uma API única para listar templates
Vite e Expo. O objetivo é descobrir opções adicionais sem transformar um
resultado de busca pública em comando arbitrário.

## Decisão

Adotar um **catálogo híbrido**:

1. **Presets locais verificados:** continuar listando os oito presets de
   `create-vite --template` e `create-expo-app --template`. A interface pode
   exibi-los sem consultas HTTP.
2. **Exemplos Expo oficiais:** consultar o endpoint fixo
   `GET https://api.github.com/repos/expo/examples/contents`, aceitando somente
   diretórios `with-*` na raiz com URL canônica de `expo/examples`. A estratégia
   de criação é `create-expo-app --example <id>` com argumentos separados.
3. **Descoberta comunitária Vite:** usar a GitHub Search API sob demanda,
   rotular a origem como externa e **desabilitar a geração automática**. O link é
   fornecido para investigação; a pesquisa não equivale a aprovação de template.
4. **Idioma e compatibilidade:** a linguagem de exemplos Expo é definida pelos
   arquivos do exemplo e **não pode ser garantida** pela opção JS/TS escolhida.
   Presets locais permanecem estritamente filtrados por idioma.
5. **Desempenho:** workers `QRunnable` com sinais Qt, debounce de 650 ms,
   timeout HTTP e cache de 600 s em memória. A busca não afeta o pipeline de
   geração, instalação opcional de bibliotecas e abertura de IDE.
6. **Segurança:** validar slug, URL, origem e estratégia dentro do núcleo.
   Nenhuma entrada externa pode fornecer nome de executável, flags arbitrárias
   ou script de instalação. Não inserir tokens do GitHub no código/executável.
7. **Resiliência:** respostas vazias, rate limits e ausência de rede produzem
   aviso; catálogo local continua acessível quando se limpa o filtro. A
   geração real ainda pode requerer npm e conexão.

## Alternativas analisadas

- **Catálogo 100% estático:** simples e seguro, mas dificulta a descoberta.
- **Clonagem arbitrária de repositórios de busca:** rejeitada devido a
  procedência, scripts de instalação e compatibilidade não auditados.
- **API/backend próprio:** adiciona custos operacionais e não é necessário no MVP.
- **Buscar qualquer template npm e executar:** rejeitado nesta etapa porque um
  pacote npm não é necessariamente um template válido do Vite ou Expo.

## Consequências e limites

- GitHub pode limitar requisições anônimas (inclusive pesquisa); cache reduz
  chamadas, mas não garante disponibilidade.
- Expo/examples pode adicionar, renomear ou remover exemplos. O CLI decide se o
  exemplo continua válido; não há bloqueio de versão de SDK.
- O RNPB não garante licença, manutenção, segurança ou funcionalidade de
  repositórios externos. Usuários devem revisar o projeto e suas dependências.
- A UI distinguirá claramente referências de opções instaláveis.
- Não há autenticação opcional, importação de template comunitário, catálogo npm
  nem execução offline garantida neste ADR. São extensões futuras que exigem
  propostas próprias.
