# Rodix Football — pacote para as lojas

App ID (Android e iOS): `com.rodix.football`  (troque em capacitor.config.json, android/app/build.gradle e no Xcode antes do 1º envio, se quiser outro)
Orientação: paisagem. Funciona offline. Sem anúncios, sem compras, sem coleta de dados (salvamento só no aparelho).

## 0. Colocar na nuvem de build (uma vez)
1. Crie um repositório PRIVADO no GitHub e envie esta pasta inteira.
2. Settings > Secrets and variables > Actions > New repository secret (valores abaixo).

## 1. Android (Google Play)
1. Crie a chave de envio (no seu computador, uma vez):
   `keytool -genkeypair -v -keystore upload.jks -alias rodix -keyalg RSA -keysize 2048 -validity 10000`
   Guarde o arquivo e as senhas em lugar seguro. Perder a chave de envio dá trabalho para recuperar.
2. Secrets: ANDROID_KEYSTORE_BASE64 (`base64 -w0 upload.jks`), ANDROID_KEYSTORE_PASSWORD, ANDROID_KEY_ALIAS (rodix), ANDROID_KEY_PASSWORD.
3. Actions > "Android AAB" > Run workflow. Baixe o `rodix-football-aab`.
4. Play Console > Criar app > preencha: Política de privacidade (URL), Segurança dos dados, Classificação etária, Público-alvo, Anúncios = não.
5. Teste e lançamento > Testes > Pré-registro: envie o AAB na faixa de pré-registro, complete o anúncio da loja (textos em STORE_LISTING.md), escolha países e inicie.
   Conta pessoal nova: pode exigir teste fechado antes (a Play Console mostra).
6. Na data: publique na faixa Produção; os pré-registrados são notificados.

## 2. iOS (App Store)
1. App Store Connect > Usuários e Acesso > Integrações > chave de API (função "App Manager"). Baixe o .p8.
2. App Store Connect > Apps > + Novo app: nome Rodix Football, ID do pacote com.rodix.football (cadastre antes em developer.apple.com > Identifiers).
3. Secrets: ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_P8_BASE64 (`base64 -w0 AuthKey_XXXX.p8`), APPLE_TEAM_ID.
4. Actions > "iOS TestFlight" > Run workflow. O build vai direto para o App Store Connect (aparece em ~15–30 min).
5. Na página da versão: anexe o build, capturas (iPhone 6,9" e iPad 13", em paisagem), textos de STORE_LISTING.md, privacidade, classificação etária, notas para o revisor.
6. Envie para revisão. Aprovado, vá em Preço e Disponibilidade > Pré-pedido: data de lançamento e regiões > Publicar.
   (A Apple só abre o pré-pedido depois que o app for aprovado.)

## Dica para a revisão da Apple (guideline 4.2)
O app é um jogo completo e offline, com carreira, partidas, competições e salvamento. Diga isso nas notas e inclua um vídeo curto de gameplay. Não é um site embrulhado.

## Atualizar o jogo
Gere o novo `soccer-champs.html`, copie para www/index.html (mantendo o bloco @font-face e sem service worker), rode `npx cap sync` e dispare os dois workflows.
