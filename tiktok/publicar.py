#!/usr/bin/env python3
"""Publica no TikTok os mesmos posts da agenda do Instagram (instagram/agenda.json).

Modos (variável MODO):
  conectar   sem CODIGO, mostra o link para autorizar o app no TikTok; com CODIGO,
             troca o código pelas chaves de acesso e guarda tudo criptografado
  verificar  confere a conexão e o próximo post da agenda, sem publicar nada
  teste      publica um post da agenda (variável POST, padrão 2026-teste-01) como privado ("Só eu");
             com ENVIO=rascunho, manda pra caixa de entrada do app em vez de publicar
  agenda     publica o próximo post cujo horário já chegou (uso normal, pelo agendamento)

Um post da agenda com "tiktok": false fica só no Instagram, e "legenda_tiktok" troca a legenda.
"""
import json
import os
import secrets
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://open.tiktokapis.com/v2"
SITE = "https://ivanfulyconsorcios.com.br/"
RETORNO = SITE + "tiktok/"
ESCOPOS = "user.info.basic,video.publish,video.upload"
PASTA = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PASTA)
AGENDA = os.path.join(RAIZ, "instagram", "agenda.json")
REGISTRO = os.path.join(PASTA, "publicados.json")
CONFIG = os.path.join(PASTA, "config.json")
CONEXAO = os.path.join(PASTA, "conexao.enc")
ATRASO_MAXIMO = timedelta(hours=6)
POST_TESTE = "2026-teste-01"
MB = 1024 * 1024

# O que fazer quando o TikTok devolve estes erros.
EXPLICACOES = {
    "unaudited_client_can_only_post_to_private_accounts":
        "Enquanto o app não for aprovado pelo TikTok, a conta precisa estar privada na hora do post "
        "(TikTok > Perfil > Menu > Configurações e privacidade > Privacidade > Conta privada).",
    "privacy_level_option_mismatch": "A privacidade de tiktok/config.json não está entre as permitidas para a conta.",
    "spam_risk_too_many_posts": "O TikTok limitou: muitos posts pelo app nas últimas 24 horas.",
    "spam_risk_too_many_pending_share": "Há rascunhos demais esperando na caixa do TikTok. Publique ou apague alguns.",
    "spam_risk_user_banned_from_posting": "A conta está impedida de postar pelo app no momento.",
    "access_token_invalid": "A conexão com o TikTok caiu. Rode o robô no modo conectar de novo.",
    "scope_not_authorized": "Falta permissão. Rode o robô no modo conectar de novo e aceite tudo.",
    "url_ownership_unverified": "O endereço da foto não está no site verificado no TikTok for Developers.",
    "rate_limit_exceeded": "Muitas chamadas seguidas. Tente de novo daqui a 1 minuto.",
}

CHAVE = ""
SEGREDO = ""
TOKEN = ""


def carregar(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return padrao


def salvar(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")


def agora_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def esconder(valor):
    """Pede pro GitHub trocar o valor por *** em qualquer log."""
    if valor and os.environ.get("GITHUB_ACTIONS"):
        print(f"::add-mask::{valor}")


def resumo(texto):
    """Escreve no resumo da execução, que aparece no topo da página dela no GitHub."""
    arquivo = os.environ.get("GITHUB_STEP_SUMMARY")
    if arquivo:
        with open(arquivo, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


def abrir(req):
    try:
        with urllib.request.urlopen(req, timeout=120) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as e:
        texto = e.read().decode(errors="replace")
        try:
            dados = json.loads(texto)
        except ValueError:
            dados = None
        if not isinstance(dados, dict) or not dados.get("error"):
            dados = {"error": {"code": f"http_{e.code}", "message": texto[:300]}}
        return dados


def chamar(caminho, corpo=None, metodo="POST"):
    dados = None if metodo == "GET" else json.dumps(corpo or {}).encode()
    req = urllib.request.Request(f"{API}/{caminho}", data=dados, method=metodo, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    })
    resposta = abrir(req)
    erro = resposta.get("error") or {}
    if erro.get("code", "ok") != "ok":
        codigo = erro.get("code")
        dica = EXPLICACOES.get(codigo, "")
        raise SystemExit(f"Erro do TikTok em {caminho.split('?')[0]}: {codigo}: {erro.get('message', '')} {dica}".strip())
    return resposta.get("data") or {}


# ---------- conexão (OAuth) ----------

def cifra(argumentos, entrada):
    """Criptografa (ou abre, com -d) usando o Client secret como senha, pra conexão poder ficar no repositório."""
    r = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt", "-a", "-A", *argumentos,
         "-pass", "env:TIKTOK_SENHA_CIFRA"],
        input=entrada, capture_output=True, env={**os.environ, "TIKTOK_SENHA_CIFRA": SEGREDO})
    if r.returncode:
        raise SystemExit("Não consegui abrir a conexão guardada do TikTok. Se o Client secret mudou, "
                         "rode o robô no modo conectar de novo.")
    return r.stdout


def guardar(conexao):
    with open(CONEXAO, "w", encoding="utf-8") as f:
        f.write(cifra([], json.dumps(conexao).encode()).decode() + "\n")


def pedir_token(**params):
    params.update(client_key=CHAVE, client_secret=SEGREDO)
    req = urllib.request.Request(f"{API}/oauth/token/", data=urllib.parse.urlencode(params).encode(), method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    r = abrir(req)
    if "access_token" not in r:
        erro, detalhe = r.get("error"), r.get("error_description", "")
        if isinstance(erro, dict):
            erro, detalhe = erro.get("code"), erro.get("message", "")
        raise SystemExit(f"O TikTok recusou a conexão: {erro}: {detalhe}")
    esconder(r["access_token"])
    esconder(r.get("refresh_token"))
    agora = int(time.time())
    return {
        "open_id": r.get("open_id"),
        "escopos": r.get("scope", ""),
        "access_token": r["access_token"],
        "access_vence": agora + int(r.get("expires_in", 0)),
        "refresh_token": r["refresh_token"],
        "refresh_vence": agora + int(r.get("refresh_expires_in", 0)),
    }


def usar_conexao():
    """Abre a conexão guardada e renova o acesso, que vale só 24 horas, quando estiver perto de vencer."""
    global TOKEN
    try:
        with open(CONEXAO, encoding="utf-8") as f:
            texto = f.read().strip()
    except FileNotFoundError:
        raise SystemExit("O TikTok ainda não foi conectado. Rode o robô no modo conectar.")
    conexao = json.loads(cifra(["-d"], texto.encode()))
    esconder(conexao["access_token"])
    esconder(conexao["refresh_token"])
    agora = time.time()
    if conexao["access_vence"] - agora < 3600:
        if conexao["refresh_vence"] < agora:
            raise SystemExit("A conexão com o TikTok venceu. Rode o robô no modo conectar de novo.")
        nova = pedir_token(grant_type="refresh_token", refresh_token=conexao["refresh_token"])
        nova["open_id"] = nova["open_id"] or conexao["open_id"]
        nova["escopos"] = nova["escopos"] or conexao["escopos"]
        conexao = nova
        guardar(conexao)
    TOKEN = conexao["access_token"]
    return conexao


def conectar(codigo):
    global TOKEN
    if not codigo:
        estado = secrets.token_urlsafe(12)
        # A chave vai escrita em %XX: é o mesmo valor pro TikTok, mas assim o GitHub não troca o link por ***.
        chave = "".join(f"%{b:02X}" for b in CHAVE.encode())
        link = ("https://www.tiktok.com/v2/auth/authorize/?client_key=" + chave + "&response_type=code"
                "&scope=" + ESCOPOS +
                "&redirect_uri=" + urllib.parse.quote(RETORNO, safe="") + "&state=" + estado)
        print("Abra este link, entre no TikTok e autorize o Ivan Fuly Posts:")
        print(link)
        print("Depois copie o código que aparecer no site e rode o robô de novo no modo conectar, com o código.")
        resumo("### Conectar o TikTok\n\n"
               f"1. [**Clique aqui para autorizar o Ivan Fuly Posts no TikTok**]({link})\n"
               "2. O site vai mostrar um código. Copie.\n"
               "3. Rode o robô de novo no modo **conectar**, colando o código no campo **codigo**.\n\n"
               "O código vale por poucos minutos.")
        return
    codigo = codigo.strip()
    if "%" in codigo:  # colado direto da barra de endereço
        codigo = urllib.parse.unquote(codigo)
    esconder(codigo)
    conexao = pedir_token(grant_type="authorization_code", code=codigo, redirect_uri=RETORNO)
    guardar(conexao)
    TOKEN = conexao["access_token"]
    nome = chamar("user/info/?fields=open_id,display_name", metodo="GET").get("user", {}).get("display_name")
    print(f"TikTok conectado: {nome}")
    resumo(f"### TikTok conectado: {nome}")
    faltando = set(ESCOPOS.split(",")) - set(conexao["escopos"].split(","))
    if faltando:
        print("Atenção: o TikTok não liberou " + ", ".join(sorted(faltando)) + ". Conecte de novo e aceite tudo.")


# ---------- publicação ----------

def tamanho_tiktok(texto):
    """O TikTok conta o limite de caracteres em UTF-16 (emoji conta 2)."""
    return len(texto.encode("utf-16-le")) // 2


def cortar(texto, limite):
    while tamanho_tiktok(texto) > limite:
        texto = texto[:-1]
    return texto.rstrip()


def dividir_legenda(legenda):
    """Foto no TikTok tem título (até 90) e descrição (até 4000): a primeira linha vira o título."""
    primeira, _, resto = legenda.strip().partition("\n")
    if tamanho_tiktok(primeira) <= 90:
        return primeira.strip(), cortar(resto.strip(), 4000)
    return cortar(primeira, 89) + "…", cortar(legenda.strip(), 4000)


def conferir_no_site(url):
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=60) as resposta:
            ok = resposta.status == 200 and resposta.url == url
    except urllib.error.URLError:
        ok = False
    if not ok:
        raise SystemExit(f"A foto ainda não está no site (o TikTok puxa de lá): {url}")


def enviar_video(caminho, url, tamanho, pedaco, partes):
    with open(caminho, "rb") as f:
        for i in range(partes):
            inicio = i * pedaco
            fim = tamanho - 1 if i == partes - 1 else inicio + pedaco - 1
            f.seek(inicio)
            bloco = f.read(fim - inicio + 1)
            req = urllib.request.Request(url, data=bloco, method="PUT", headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(len(bloco)),
                "Content-Range": f"bytes {inicio}-{fim}/{tamanho}",
            })
            try:
                with urllib.request.urlopen(req, timeout=300) as resposta:
                    resposta.read()
            except urllib.error.HTTPError as e:
                raise SystemExit(f"O TikTok recusou o envio do vídeo ({e.code}): {e.read().decode(errors='replace')[:300]}")


def iniciar(post, criador, privacidade, cfg):
    """Manda o post pro TikTok e devolve o publish_id. No modo rascunho, vai pra caixa de entrada do app."""
    rascunho = cfg.get("modo") == "rascunho"
    legenda = post.get("legenda_tiktok", post["legenda"])
    opcoes = {
        "privacy_level": privacidade,
        "disable_comment": bool(criador.get("comment_disabled")),
        "brand_organic_toggle": bool(cfg.get("marca_propria", True)),
    }
    if "video" in post:
        caminho = os.path.join(RAIZ, post["video"])
        tamanho = os.path.getsize(caminho)
        # Até 64 MB vai inteiro; acima disso, em pedaços de 10 MB (o último leva o resto).
        pedaco = tamanho if tamanho <= 64 * MB else 10 * MB
        partes = tamanho // pedaco
        fonte = {"source": "FILE_UPLOAD", "video_size": tamanho, "chunk_size": pedaco, "total_chunk_count": partes}
        if rascunho:
            dados = chamar("post/publish/inbox/video/init/", {"source_info": fonte})
        else:
            info = opcoes | {
                "title": cortar(legenda, 2200),
                "disable_duet": bool(criador.get("duet_disabled")),
                "disable_stitch": bool(criador.get("stitch_disabled")),
            }
            if "capa_ms" in post:
                info["video_cover_timestamp_ms"] = post["capa_ms"]
            dados = chamar("post/publish/video/init/", {"post_info": info, "source_info": fonte})
        enviar_video(caminho, dados["upload_url"], tamanho, pedaco, partes)
    else:
        url = SITE + post["imagem"]
        conferir_no_site(url)
        titulo, descricao = dividir_legenda(legenda)
        info = {"title": titulo, "description": descricao}
        if not rascunho:
            info |= opcoes | {"auto_add_music": True}
        dados = chamar("post/publish/content/init/", {
            "post_info": info,
            "source_info": {"source": "PULL_FROM_URL", "photo_cover_index": 0, "photo_images": [url]},
            "post_mode": "MEDIA_UPLOAD" if rascunho else "DIRECT_POST",
            "media_type": "PHOTO",
        })
    return dados["publish_id"]


def esperar(publish_id):
    for _ in range(60):  # até 5 minutos
        estado = chamar("post/publish/status/fetch/", {"publish_id": publish_id})
        if estado.get("status") in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            return estado
        if estado.get("status") == "FAILED":
            raise SystemExit(f"O TikTok não publicou: {estado.get('fail_reason')}")
        time.sleep(5)
    raise SystemExit("O TikTok ainda está processando o post. Confira no app daqui a pouco.")


def publicar(chave, post, criador, privacidade, cfg, registro):
    if cfg.get("modo") != "rascunho" and privacidade not in criador.get("privacy_level_options", []):
        raise SystemExit(f"A privacidade {privacidade} não está liberada pra esta conta agora. "
                         f"Opções do TikTok: {', '.join(criador.get('privacy_level_options', []))}. "
                         + EXPLICACOES["unaudited_client_can_only_post_to_private_accounts"])
    publish_id = iniciar(post, criador, privacidade, cfg)
    if cfg.get("modo") == "rascunho":
        privacidade = "rascunho"  # quem escolhe a privacidade é você, no app, ao publicar
    # Registra antes de esperar: se o TikTok demorar, a próxima execução não manda o mesmo post de novo.
    registro[chave] = {"status": "enviado", "publish_id": publish_id, "privacidade": privacidade, "em": agora_iso()}
    salvar(REGISTRO, registro)
    try:
        estado = esperar(publish_id)
    except SystemExit as e:
        registro[chave]["status"] = "falhou"
        registro[chave]["motivo"] = str(e)
        salvar(REGISTRO, registro)
        raise
    registro[chave]["status"] = "na caixa de entrada do TikTok" if estado["status"] == "SEND_TO_USER_INBOX" else "publicado"
    ids = estado.get("publicaly_available_post_id") or []
    if ids:
        tipo = "video" if "video" in post else "photo"
        registro[chave]["link"] = f"https://www.tiktok.com/@{criador.get('creator_username')}/{tipo}/{ids[0]}"
    salvar(REGISTRO, registro)
    print(f"{registro[chave]['status'].capitalize()}: {post['id']} ({privacidade}) {registro[chave].get('link', '')}".rstrip())


def main():
    global CHAVE, SEGREDO
    modo = os.environ.get("MODO", "agenda").strip() or "agenda"
    cfg = carregar(CONFIG, {})
    if modo == "agenda" and not cfg.get("ligado"):
        print("A publicação automática no TikTok está desligada (tiktok/config.json). Nada foi publicado.")
        return
    CHAVE = os.environ.get("TIKTOK_CLIENT_KEY", "").strip()
    SEGREDO = os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
    if not CHAVE or not SEGREDO:
        raise SystemExit("Faltam os segredos TIKTOK_CLIENT_KEY e TIKTOK_CLIENT_SECRET no GitHub "
                         "(Settings > Secrets and variables > Actions).")
    if modo == "conectar":
        conectar(os.environ.get("CODIGO", ""))
        return

    agenda = carregar(AGENDA, [])
    registro = carregar(REGISTRO, {})
    pendentes = sorted((p for p in agenda if p.get("tiktok", True) and p["id"] not in registro),
                       key=lambda p: p["quando"])

    if modo == "teste":
        if os.environ.get("ENVIO", "").strip() == "rascunho":
            cfg["modo"] = "rascunho"
        alvo = os.environ.get("POST", "").strip() or POST_TESTE
        post = next((p for p in agenda if p["id"] == alvo), None)
        if not post:
            raise SystemExit(f"Não achei o post {alvo} em instagram/agenda.json.")
        usar_conexao()
        criador = chamar("post/publish/creator_info/query/")
        print(f"Conta do TikTok: @{criador.get('creator_username')}")
        publicar(f"teste:{post['id']}", post, criador, "SELF_ONLY", cfg, registro)
        return

    if modo == "verificar":
        usar_conexao()
        criador = chamar("post/publish/creator_info/query/")
        print(f"Conta do TikTok: @{criador.get('creator_username')} ({criador.get('creator_nickname')})")
        print("Privacidades liberadas agora: " + ", ".join(criador.get("privacy_level_options", [])))
        print(f"Privacidade configurada: {cfg.get('privacidade', 'SELF_ONLY')}. Modo: {cfg.get('modo', 'direto')}.")
        if pendentes:
            post = pendentes[0]
            if "video" in post:
                if not os.path.exists(os.path.join(RAIZ, post["video"])):
                    raise SystemExit(f"Falta o vídeo do post {post['id']}: {post['video']}")
            else:
                conferir_no_site(SITE + post["imagem"])
            print(f"Próximo post: {post['id']} em {post['quando']}. A mídia está no lugar.")
        else:
            print("Nenhum post pendente na agenda.")
        print("Nada foi publicado.")
        return

    # modo agenda: só fala com o TikTok quando tem post no horário
    agora = datetime.now(timezone.utc)
    for post in pendentes:
        quando = datetime.fromisoformat(post["quando"])
        if quando > agora:
            print(f"Próximo post: {post['id']} em {post['quando']}.")
            return
        if agora - quando > ATRASO_MAXIMO:
            registro[post["id"]] = {"status": "pulado", "motivo": "passou mais de 6 horas do horário", "em": agora_iso()}
            salvar(REGISTRO, registro)
            print(f"Pulado por atraso: {post['id']} ({post['quando']}).")
            continue
        usar_conexao()
        criador = chamar("post/publish/creator_info/query/")
        publicar(post["id"], post, criador, cfg.get("privacidade", "SELF_ONLY"), cfg, registro)
        return  # no máximo um post por execução
    print("Não há posts pendentes na agenda.")


if __name__ == "__main__":
    main()
