# ivanfulyconsorcios.com.br

Site do Ivan Fuly, consultor de consórcios no Rio de Janeiro.

- `index.html`: a página inteira (textos, estilo e scripts).
- Número do WhatsApp: constante `WHATSAPP_NUMBER` no início do script em `index.html` (só números, com 55 e DDD).
- `CNAME`: domínio usado pelo GitHub Pages.
- `og-image.png`: imagem que aparece quando o link é compartilhado no WhatsApp e nas redes.

## Robô do Instagram

- `instagram/agenda.json`: posts agendados (horário, imagem e legenda).
- `instagram/semana-NN/`: imagens dos posts em JPG.
- `instagram/config.json`: `"ligado": true` liga a publicação automática; `false` desliga.
- `instagram/publicados.json`: registro do que já foi publicado (o robô atualiza sozinho).
- `.github/workflows/instagram.yml`: roda a cada 20 minutos, das 11h às 21h (horário de Brasília), e publica o post cujo horário chegou.
- O token fica no segredo `IG_ACCESS_TOKEN` (Settings > Secrets and variables > Actions) e vence em cerca de 60 dias.
- Para testar sem publicar: Actions > Publicar no Instagram > Run workflow > modo `verificar`.
