# ADR-0002 — Integração opcional com editores locais

- **Data:** 06/11/2026
- **Status:** Aceito para implementação na issue #12; sujeito a revisão e merge do PR.
- **Depende de:** PR #9 (wizard de criação, bibliotecas e validações).

## Contexto
O RNPB cria projetos Vite/Expo sem exigir comandos manuais, mas o usuário precisa
localizar e abrir o projeto em sua IDE depois do processo. A aplicação deve respeitar
instalações em pastas personalizadas e não assumir que \`code .\` esteja configurado.

## Decisão
1. Criar \`core/editor_manager.py\`, sem Qt: detecta **VS Code** e **Android Studio**
   pelo PATH, instalações convencionais e Registro do Windows (App Paths).
2. Permitir seleção manual **apenas de executáveis esperados** desses editores.
   Os caminhos são validados na seleção e novamente antes de abrir.
3. Salvar preferência e habilitação da abertura automática com \`QSettings\`
   por usuário, isolando persistência e widgets em \`ui/editor_settings.py\`.
4. Abrir a raiz do projeto por \`subprocess.Popen([executável, diretório])\`, sem
   shell ou composição de comandos. Nunca abrir antes da conclusão das etapas.
5. Abrir somente após resultado final bem-sucedido. O botão manual é disponibilizado
   nos Logs após sucesso. A abertura automática é desativada por padrão.
6. Falhas na detecção/abertura geram aviso, **nunca falha da geração**.
   Ausência de IDE não bloqueia o usuário.

## Consequências
- O projeto Expo gerenciado, normalmente sem \`android/\`, abre a raiz; o RNPB
  não invoca prebuild nem instala ferramentas/emuladores.
- Na primeira fase a detecção é prioritariamente **Windows**. Suporte de outros
  sistemas fica sujeito a testes reais com diferentes instalações.
- A aplicação pode abrir um executável explicitamente escolhido pelo usuário:
  valida nome esperado e invoca sem shell, mas não autentica a origem do binário.
- \`QSettings\` é adequado para preferências simples; o plano anterior de JSON
  com \`platformdirs\` continua válido para o futuro cache de APIs e catálogos.
- A implementação é feita sobre o wizard do PR #9 e deve ter um PR próprio para
  revisão, sem merge antecipado na \`main\`.

## Alternativas
- Apenas \`code .\`: descartado por depender do PATH e suportar somente VS Code.
- Buscar recursivamente todas as unidades: descartado por custo, lentidão e privacidade.
- Executar \`shell=True\` ou concatenar comando: descartado por risco de injeção.
- Instalar IDE automaticamente: fora do escopo; consentimento e licenças adicionais.
