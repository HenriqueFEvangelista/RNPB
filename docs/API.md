# APIs e integrações do RNPB

**Versão:** proposta inicial — 31/10/2026  
**Status:** npm Registry e React Native Directory **implementados no PR #9**, ainda em revisão. GitHub REST API permanece planejada.

Esta documentação descreve fontes externas para descobrir bibliotecas e templates e distingue **APIs HTTP** de **ferramentas de linha de comando**. O RNPB é uma aplicação desktop; não está prevista uma API HTTP própria para o MVP.

## 1. Visão geral

| Serviço / ferramenta | Papel no RNPB | Autenticação | Abordagem |
| --- | --- | --- | --- |
| [npm Registry](https://api-docs.npmjs.com/) | Busca e metadados de pacotes JavaScript | Leitura pública sem chave | API principal de pacotes |
| [React Native Directory](https://github.com/react-native-community/directory/blob/main/API.md) | Metadados e filtros de compatibilidade para React Native/Expo | Consultas públicas, sujeitas à disponibilidade do serviço | Complemento ao npm |
| [GitHub REST API](https://docs.github.com/en/rest) | Descoberta opcional de templates/exemplos públicos | Consulta pública sem token; token opcional aumenta limites | Uso controlado com cache |
| [Vite](https://vite.dev/guide/) | Gerar projetos React web | Não aplicável | Comando local via npm |
| [Expo](https://docs.expo.dev/more/create-expo/) | Gerar e executar projetos React Native | Não aplicável à geração local | Comando local via npx |
| [Expo Tunnel](https://docs.expo.dev/get-started/start-developing/) | Conectar Expo Go ao servidor em redes diferentes | Pode depender do serviço de túnel | Ferramenta opcional, não API REST |

## 1.1 Implementação em código (PR #9)

- `core/package_catalog.py` consulta o npm Registry e React Native Directory via `requests`, com timeout e fallback parcial.
- `core/packages.py` normaliza nome, versão, descrição, categoria e indicadores de compatibilidade.
- `ui/catalog_worker.py` executa consultas HTTP por `QRunnable` e sinais Qt; o formulário usa debounce de **450 ms** e descarta resultados obsoletos.
- O cache atual dura **600 segundos e é somente em memória**. Não há ainda persistência nem paginação de resultados.
- O React Native Directory fornece indicadores `expoGo`, `android`, `ios` e `web`, mas só o filtro **Somente Expo Go** está disponível no formulário nesta etapa.
- Pacotes retornados somente pelo npm no contexto React Native possuem compatibilidade **desconhecida**; o sistema não supõe compatibilidade positiva.
- A instalação opcional ocorre depois da geração e dependências-base do Vite, via `core/package_installer.py`, usando comandos Qt sem interpolar shell.

## 2. npm Registry — pesquisa de bibliotecas

**Endpoint de pesquisa:**

~~~http
GET https://registry.npmjs.org/-/v1/search?text=zustand&size=10
~~~

**Parâmetros usados inicialmente:**
- `text`: termo de pesquisa; codificar como parâmetro de URL.
- `size`: número de resultados solicitados; impor limite local para evitar consultas excessivas.

**Campos de interesse:** `objects[].package.name`, `version`, `description`, `links` e metadados disponíveis. O aplicativo deve tolerar campos opcionais ausentes.

**Consulta pontual de pacote:**

~~~http
GET https://registry.npmjs.org/axios
~~~

**Uso planejado:** preencher nome, versão, descrição, link oficial e comando de instalação, após validação da escolha do usuário. Existir no npm **não prova** que um pacote funciona com React Native ou Expo Go.

## 3. React Native Directory — compatibilidade

**Exemplo de consulta:**

~~~http
GET https://reactnative.directory/api/libraries?search=image&limit=20&skipTools=true
~~~

**Objetivo:** complementar os resultados do npm com filtros/indicadores de plataformas (como Android, iOS e web) e compatibilidade informada com Expo Go, conforme os campos retornados pela API.

**Cuidados:**
- Tratar o catálogo como fonte auxiliar, sujeita a mudanças de esquema e disponibilidade.
- A indicação `expoGo=true` não garante compatibilidade em todo SDK, versão do pacote ou dispositivo.
- Não misturar automaticamente resultados do diretório com pacotes npm homônimos sem validar a identificação.
- Em falha da API, permitir consulta npm com um aviso de que a compatibilidade não foi verificada.

## 4. GitHub REST API — descoberta de templates

**Exemplo: listar o conteúdo público do repositório de exemplos do Expo:**

~~~http
GET https://api.github.com/repos/expo/examples/contents
~~~

A resposta da API de conteúdo apresenta arquivos e diretórios; o RNPB pode exibir exemplos selecionados com origem e documentação. Repositórios encontrados em buscas não serão tratados automaticamente como templates seguros, executáveis ou compatíveis.

**Autenticação e limites:**
- Leitura de recursos públicos normalmente dispensa token.
- Limite primário padrão sem autenticação: **60 requisições/hora por IP**.
- Com token pessoal, o limite primário típico é **5.000 requisições/hora**, sujeito às regras aplicáveis à autenticação.
- Endpoints de **search** possuem limites próprios e podem sofrer limites secundários.
- Consultar cabeçalhos como `x-ratelimit-remaining` e `x-ratelimit-reset` e respeitar respostas HTTP `403`/`429`.
- Nunca distribuir um token pessoal embutido no executável. Se autenticação individual for adicionada, requer decisão e implementação seguras específicas.

**Estratégia do MVP:** consultar GitHub apenas sob demanda, preferir catálogo local curado, cache e validação de origem/licença. **Não** tornar o GitHub dependência obrigatória da criação básica.

Documentação: [Limites da GitHub REST API](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

## 5. Ferramentas locais (não são APIs HTTP)

Os comandos seguintes são exemplos de execução pelo núcleo do RNPB, com argumentos seguros e diretório de trabalho controlado.

**React web — Vite:**

~~~bash
npm create vite@latest meu-app -- --template react
npm create vite@latest meu-app -- --template react-ts
~~~

**React Native — Expo:**

~~~bash
npx create-expo-app@latest meu-app --template blank
npx create-expo-app@latest meu-app --template blank-typescript
~~~

Outras opções do Expo, como `default` e `tabs`, devem ser expostas apenas nas combinações de linguagem suportadas pela versão do gerador.

**Instalar bibliotecas:**

~~~bash
npm install axios zustand
npx expo install expo-sqlite
~~~

Em projetos Expo, usar `npx expo install` sempre que adequado para obter versões compatíveis com o SDK.

**Expo Go em redes distintas:**

~~~bash
npm install -g @expo/ngrok
npx expo start --tunnel
~~~

O `@expo/ngrok` é uma **ferramenta de desenvolvimento**, não uma biblioteca de runtime do aplicativo. Sua instalação global é opcional e deve ser exibida/confirmada antes da execução. O modo LAN continua disponível com `npx expo start`. Redes escolares ou corporativas podem bloquear serviços de túnel.

## 6. Contrato interno sugerido para integrações

Não se trata de uma API pública do RNPB, e sim de um modelo interno inicial, sujeito a revisão:

~~~json
{
  "name": "axios",
  "version": "versao-obtida-do-registro",
  "description": "Biblioteca HTTP",
  "source": "npm",
  "supported_targets": ["react", "react-native"],
  "expo_go_compatibility": "unknown",
  "install_strategy": "npm"
}
~~~

- `supported_targets` só deve ser preenchido quando houver validação; do contrário, manter estado desconhecido.
- `expo_go_compatibility`: `compatible`, `incompatible` ou `unknown` (metadado, não garantia).
- `install_strategy`: `npm` ou `expo`, determinado por regra do projeto e revisão da biblioteca.
- Registrar de onde cada informação veio e quando foi atualizada.

## 7. Cache, resiliência e segurança

- Manter **catálogo local** para templates oficiais e ferramentas populares revisadas.
- Cachear pesquisas e metadados por prazo configurável; uma sugestão inicial é 30 minutos para buscas e 24 horas para listas de exemplos, sujeita a testes.
- Usar timeout, mensagens de erro, respeito a rate limits e tentativas limitadas com backoff para falhas transitórias.
- Revalidar a compatibilidade e os comandos na versão atual de Vite/Expo antes de apresentá-los como disponíveis.
- Validar identificadores de pacotes, nomes de projeto, caminhos e origens. Evitar execução automática de scripts/repositórios desconhecidos.
- Comandos do sistema devem usar **lista de argumentos**, sem concatenação de strings fornecidas pelo usuário em um shell.
- Operações HTTP e de CLI não podem bloquear a interface gráfica: a arquitetura aprovada é **PySide6**, com **QProcess** para CLI e **workers Qt** para HTTP, conforme [ADR-0001](./ADR/0001-arquitetura-e-geradores.md) e [ARQUITETURA.md](./ARQUITETURA.md). O fluxo Qt/QProcess e os workers HTTP estão implementados no PR #9; recursos extras e cache persistente permanecem pendentes.

## 8. Referências

- [npm Registry API](https://api-docs.npmjs.com/)
- [React Native Directory API](https://github.com/react-native-community/directory/blob/main/API.md)
- [GitHub REST API](https://docs.github.com/en/rest)
- [Vite — Getting Started](https://vite.dev/guide/)
- [Expo — Create a project](https://docs.expo.dev/more/create-expo/)
- [Expo — Start developing](https://docs.expo.dev/get-started/start-developing/)

> Esta é uma proposta de integração. Os endpoints, limites e templates podem mudar; confirmar documentação oficial e respostas reais durante a implementação.
