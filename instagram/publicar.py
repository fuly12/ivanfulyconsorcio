#!/usr/bin/env python3
"""Publica no Instagram os posts da agenda, usando a API do Instagram com login do Instagram.

Modos (variável MODO):
  agenda     publica o próximo post cujo horário já chegou (uso normal, pelo agendamento)
  verificar  confere o token e testa o próximo post de imagem e os vídeos da agenda, sem publicar nada
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.instagram.com"
PASTA = os.path.dirname(os.path.abspath(__file__))
AGENDA = os.path.join(PASTA, "agenda.json")
REGISTRO = os.path.join(PASTA, "publicados.json")
CONFIG = os.path.join(PASTA, "config.json")
# Um post que ficou para trás mais que isso (robô parado, token vencido) é pulado
# em vez de sair fora de hora.
ATRASO_MAXIMO = timedelta(hours=6)

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


def chamar(metodo, caminho, **params):
    params["access_token"] = TOKEN
    corpo = urllib.parse.urlencode(params)
    if metodo == "GET":
        req = urllib.request.Request(f"{API}/{caminho}?{corpo}")
    else:
        req = urllib.request.Request(f"{API}/{caminho}", data=corpo.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as e:
        texto = e.read().decode(errors="replace")
        try:
            erro = json.loads(texto).get("error", {})
            msg = f"{erro.get('type', '')} {erro.get('code', '')}: {erro.get('message', texto)}"
        except ValueError:
            msg = texto[:300]
        raise SystemExit(f"Erro da API do Instagram ({e.code}) em {metodo} {caminho}: {msg}")


def url_da_midia(caminho):
    base = carregar(CONFIG, {}).get("base_midia")
    if not base:
        repo = os.environ.get("GITHUB_REPOSITORY", "fuly12/ivanfulyconsorcio")
        versao = os.environ.get("GITHUB_SHA", "main")
        base = f"https://raw.githubusercontent.com/{repo}/{versao}/"
    return base + caminho


def preparar(ig_id, post):
    """Cria o conteiner de mídia (ainda não publica) e espera o Instagram processar a imagem ou o vídeo."""
    if "video" in post:
        params = {"media_type": "REELS", "video_url": url_da_midia(post["video"]), "share_to_feed": "true"}
        if "capa_ms" in post:
            params["thumb_offset"] = post["capa_ms"]
        tentativas = 72  # vídeo demora mais para processar (até 6 minutos)
    else:
        params = {"image_url": url_da_midia(post["imagem"])}
        tentativas = 24
    conteiner = chamar("POST", f"{ig_id}/media", caption=post["legenda"], **params)["id"]
    for _ in range(tentativas):
        estado = chamar("GET", conteiner, fields="status_code,status")
        codigo = estado.get("status_code")
        if codigo == "FINISHED":
            return conteiner
        if codigo in ("ERROR", "EXPIRED"):
            raise SystemExit(f"O Instagram recusou o post {post['id']}: {estado.get('status', codigo)}")
        time.sleep(5)
    raise SystemExit(f"O Instagram demorou demais para processar a mídia do post {post['id']}.")


def agora_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main():
    global TOKEN
    TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not TOKEN:
        raise SystemExit("Falta o segredo IG_ACCESS_TOKEN no GitHub (Settings > Secrets and variables > Actions).")
    modo = os.environ.get("MODO", "agenda").strip() or "agenda"

    agenda = carregar(AGENDA, [])
    registro = carregar(REGISTRO, {})
    pendentes = sorted((p for p in agenda if p["id"] not in registro), key=lambda p: p["quando"])

    conta = chamar("GET", "me", fields="user_id,username")
    ig_id = conta.get("user_id") or conta["id"]
    print(f"Conta conectada: @{conta.get('username')}")

    if modo == "verificar":
        if not pendentes:
            print("Token OK. Nenhum post pendente na agenda.")
            return
        # Testa o próximo post de imagem e todos os vídeos pendentes, sem publicar nada.
        imagens = [p for p in pendentes if "video" not in p][:1]
        videos = [p for p in pendentes if "video" in p]
        for post in imagens + videos:
            preparar(ig_id, post)
            tipo = "o vídeo" if "video" in post else "a imagem"
            print(f"Tudo certo: o Instagram aceitou {tipo} e a legenda do post {post['id']} ({post['quando']}).")
        print("Nada foi publicado.")
        return

    if not carregar(CONFIG, {}).get("ligado"):
        print("A publicação automática está desligada (instagram/config.json). Nada foi publicado.")
        return

    agora = datetime.now(timezone.utc)
    for post in pendentes:
        quando = datetime.fromisoformat(post["quando"])
        if quando > agora:
            print(f"Próximo post: {post['id']} em {post['quando']}.")
            break
        if agora - quando > ATRASO_MAXIMO:
            registro[post["id"]] = {"status": "pulado", "motivo": "passou mais de 6 horas do horário", "em": agora_iso()}
            salvar(REGISTRO, registro)
            print(f"Pulado por atraso: {post['id']} ({post['quando']}).")
            continue
        conteiner = preparar(ig_id, post)
        midia = chamar("POST", f"{ig_id}/media_publish", creation_id=conteiner)
        registro[post["id"]] = {"status": "publicado", "media_id": midia["id"], "em": agora_iso()}
        salvar(REGISTRO, registro)
        try:
            link = chamar("GET", midia["id"], fields="permalink").get("permalink")
        except SystemExit:
            link = None
        if link:
            registro[post["id"]]["link"] = link
            salvar(REGISTRO, registro)
        print(f"Publicado: {post['id']} -> {link or midia['id']}")
        break  # no máximo um post por execução
    else:
        print("Não há posts pendentes na agenda.")


if __name__ == "__main__":
    main()
