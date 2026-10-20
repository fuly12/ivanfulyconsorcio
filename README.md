# ivanfulyconsorcios.com.br

Site do Ivan Fuly, consultor de consórcios no Rio de Janeiro.

- `index.html`: a página inteira (textos, estilo e scripts).
- Número do WhatsApp: constante `WHATSAPP_NUMBER` no início do script em `index.html` (só números, com 55 e DDD).
- Pixel da Meta: constante `PIXEL_ID` no script de `index.html`. Só carrega depois que o visitante toca em "Pode" no aviso de cookies; conta as visitas (`PageView`) e os toques nos botões do WhatsApp (`Contact`). Não mexe nos anúncios.
- `CNAME`: domínio usado pelo GitHub Pages.
- `og-image.png`: imagem que aparece quando o link é compartilhado no WhatsApp e nas redes.

## Robô do Instagram

- `instagram/agenda.json`: posts agendados (horário, imagem e legenda).
- `instagram/semana-NN/`: imagens dos posts em JPG.
- `instagram/videos/`: vídeos (Reels) em MP4.
- `instagram/config.json`: `"ligado": true` liga a publicação automática; `false` desliga.
- `instagram/publicados.json`: registro do que já foi publicado (o robô atualiza sozinho).
- `.github/workflows/instagram.yml`: roda a cada 20 minutos, das 11h às 22h (horário de Brasília), e publica o post (imagem ou vídeo) cujo horário chegou.
- O token fica no segredo `IG_ACCESS_TOKEN` (Settings > Secrets and variables > Actions) e vence em cerca de 60 dias.
- Para testar sem publicar: Actions > Publicar no Instagram > Run workflow > modo `verificar`.

## Robô do TikTok

- Publica no TikTok os mesmos posts de `instagram/agenda.json`. Um post com `"tiktok": false` fica só no Instagram, e `"legenda_tiktok"` troca a legenda.
- `tiktok/config.json`: `"ligado"` liga a publicação automática; `"privacidade"` é `SELF_ONLY` (só eu) até o TikTok aprovar o app; `"modo": "rascunho"` manda o post pra caixa de entrada do app em vez de publicar direto; `"marca_propria"` marca o post como divulgação do próprio negócio.
- `tiktok/publicados.json`: registro do que já foi enviado (o robô atualiza sozinho).
- `tiktok/conexao.enc`: a conexão com a conta, criptografada com o Client secret (o robô renova sozinho).
- `.github/workflows/tiktok.yml`: roda nos mesmos horários do Instagram, 5 minutos depois.
- Segredos: `TIKTOK_CLIENT_KEY` e `TIKTOK_CLIENT_SECRET` (Settings > Secrets and variables > Actions).
- Para conectar a conta: Actions > Publicar no TikTok > Run workflow > modo `conectar` (sem código mostra o link; depois rode de novo colando o código que o site mostrar).
- Para testar: modo `verificar` (não publica) ou modo `teste` (publica um post como privado).
- Fotos são puxadas do site (`https://ivanfulyconsorcios.com.br/`, verificado no TikTok pelos arquivos `tiktok*.txt` na raiz).

## Robô dos anúncios (Meta)

- `anuncios/meta.py` e `.github/workflows/anuncios.yml`: rodam só quando chamados (Actions > Anúncios da Meta > Run workflow).
- Modos: `verificar` (o que a chave enxerga, inclusive os pixels), `criar` (cria a campanha, os conjuntos e os anúncios de `anuncios/plano.json` que ainda não existem, todos pausados), `ligar` (liga a campanha do plano, só quando o Ivan pede), `excluir_anterior` (exclui a campanha anterior, só depois que a nova estiver ligada), `modelo` (grava em `anuncios/modelo.json` como a Meta guardou um anúncio feito à mão) e `relatorio` (gasto, alcance, cliques e custo por clique de cada anúncio, onde os cliques aconteceram e quantas visitas e toques no WhatsApp o Pixel contou no site).
- A chave fica no segredo `META_ADS_TOKEN`. O robô não liga anúncio nem mexe em verba de nada que esteja rodando.
- Regra: campanha ligada não se altera. O que não serve se desliga, e o novo nasce do zero numa campanha nova (em `plano.json`, `campanha` vazio cria uma nova com o nome de `nome_da_campanha`). O robô pula qualquer conjunto que estiver ligado.
- `anuncios/criados.json`: registro do que o robô criou na campanha atual; `criados-campanha-1.json` guarda o da primeira campanha.
