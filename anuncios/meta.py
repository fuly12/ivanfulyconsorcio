#!/usr/bin/env python3
"""Robô dos anúncios: fala com a API de Marketing da Meta pelo GitHub.

Modos (variável MODO):
  verificar  mostra o que a chave enxerga: contas de anúncios, páginas, Instagram e campanhas
  modelo     mostra como a Meta guardou um anúncio feito à mão (variável ANUNCIO = nome ou id)
             e grava em anuncios/modelo.json, pra servir de molde pros próximos
  criar      cria os conjuntos e anúncios de anuncios/plano.json que ainda não existem, todos PAUSADOS
             (variável LIMITE = quantos anúncios no máximo nesta rodada; vazio = todos)
  relatorio  gasto, alcance, cliques e custo por clique de cada anúncio, e onde os cliques aconteceram
             (Instagram, Facebook, apps parceiros...) (variável PERIODO)

Nada aqui liga anúncio: o que o robô cria fica pausado até você ligar no Gerenciador.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.facebook.com/v23.0"
PASTA = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(PASTA, "modelo.json")
PLANO = os.path.join(PASTA, "plano.json")
CRIADOS = os.path.join(PASTA, "criados.json")
ARTES = os.path.join(PASTA, "artes")
PERIODOS = {"hoje": "today", "ontem": "yesterday", "7dias": "last_7d", "30dias": "last_30d", "tudo": "maximum"}
STATUS_CONTA = {1: "ativa", 2: "desativada", 3: "pagamento pendente", 7: "em análise", 9: "em período de carência",
                100: "fechamento pendente", 101: "fechada"}

TOKEN = ""


def resumo(texto):
    arquivo = os.environ.get("GITHUB_STEP_SUMMARY")
    if arquivo:
        with open(arquivo, "a", encoding="utf-8") as f:
            f.write(texto + "\n")


# Erros de "chamadas demais": a conta com acesso limitado à API aguenta poucas chamadas por hora.
LIMITE_DE_CHAMADAS = {4, 17, 32, 613, 80000, 80003, 80004, 80014}


def chamar(metodo, caminho, **params):
    for espera in (60, 180, 300, None):
        try:
            return _chamar(metodo, caminho, **params)
        except LimiteDeChamadas:
            if espera is None:
                raise SystemExit("A Meta segurou o robô por excesso de chamadas. Rode de novo daqui a uma hora.")
            print(f"A Meta pediu uma pausa (chamadas demais). Esperando {espera} segundos...")
            time.sleep(espera)


class LimiteDeChamadas(Exception):
    pass


def _chamar(metodo, caminho, **params):
    params = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in params.items()}
    params["access_token"] = TOKEN
    corpo = urllib.parse.urlencode(params)
    url = caminho if caminho.startswith("https://") else f"{API}/{caminho}"
    if metodo == "GET":
        req = urllib.request.Request(url if "?" in url else f"{url}?{corpo}")
    else:
        req = urllib.request.Request(url, data=corpo.encode(), method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=90) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as e:
        texto = e.read().decode(errors="replace")
        try:
            erro = json.loads(texto).get("error", {})
            if erro.get("code") in LIMITE_DE_CHAMADAS:
                raise LimiteDeChamadas()
            msg = erro.get("error_user_msg") or erro.get("message", texto)
            msg = f"{erro.get('type', '')} {erro.get('code', '')}/{erro.get('error_subcode', '')}: {msg}"
        except ValueError:
            msg = texto[:300]
        raise SystemExit(f"Erro da API da Meta ({e.code}) em {metodo} {caminho.split('?')[0]}: {msg}")


def listar(caminho, **params):
    """Junta todas as páginas de uma lista da API."""
    pagina = chamar("GET", caminho, limit=100, **params)
    itens = pagina.get("data", [])
    while pagina.get("paging", {}).get("next"):
        pagina = chamar("GET", pagina["paging"]["next"])
        itens += pagina.get("data", [])
    return itens


def brl(valor):
    return f"R$ {valor:.2f}".replace(".", ",")


def reais(centavos):
    return brl(int(centavos) / 100) if centavos else "-"


def verificar():
    eu = chamar("GET", "me", fields="id,name")
    print(f"Chave de: {eu.get('name')} ({eu['id']})")
    try:
        permissoes = [p["permission"] for p in listar("me/permissions") if p.get("status") == "granted"]
        print("Permissões: " + ", ".join(permissoes))
    except SystemExit:
        pass
    linhas = ["### O que a chave enxerga", ""]

    paginas = listar("me/accounts", fields="id,name,instagram_business_account{id,username}")
    for p in paginas:
        ig = p.get("instagram_business_account") or {}
        texto = f"Página: {p['name']} ({p['id']})" + (f" com Instagram @{ig.get('username')} ({ig.get('id')})" if ig else "")
        print(texto)
        linhas.append(f"- {texto}")
    if not paginas:
        print("Nenhuma página liberada pra esta chave.")

    contas = listar("me/adaccounts", fields="id,name,account_status,currency,timezone_name,business{id,name}")
    if not contas:
        print("Nenhuma conta de anúncios liberada pra esta chave.")
    for c in contas:
        texto = (f"Conta de anúncios: {c.get('name')} ({c['id']}), {STATUS_CONTA.get(c.get('account_status'), c.get('account_status'))}, "
                 f"{c.get('currency')}, {c.get('timezone_name')}")
        print(texto)
        linhas += [f"- {texto}", ""]
        for camp in listar(f"{c['id']}/campaigns", fields="id,name,effective_status,objective,special_ad_categories"):
            print(f"  Campanha: {camp['name']} ({camp['id']}) {camp['effective_status']} {camp.get('objective')} "
                  f"{','.join(camp.get('special_ad_categories', []))}")
            linhas.append(f"  - Campanha **{camp['name']}** ({camp['effective_status']})")
            for cj in listar(f"{camp['id']}/adsets", fields="id,name,effective_status,daily_budget,optimization_goal"):
                print(f"    Conjunto: {cj['name']} ({cj['id']}) {cj['effective_status']} {reais(cj.get('daily_budget'))}/dia "
                      f"{cj.get('optimization_goal')}")
                linhas.append(f"    - Conjunto **{cj['name']}**: {reais(cj.get('daily_budget'))}/dia ({cj['effective_status']})")
                for ad in listar(f"{cj['id']}/ads", fields="id,name,effective_status"):
                    print(f"      Anúncio: {ad['name']} ({ad['id']}) {ad['effective_status']}")
                    linhas.append(f"      - Anúncio {ad['name']} ({ad['effective_status']})")
    resumo("\n".join(linhas))


def achar_anuncio(alvo):
    if alvo.isdigit():
        return alvo
    for c in listar("me/adaccounts", fields="id"):
        for ad in listar(f"{c['id']}/ads", fields="id,name"):
            if ad["name"].strip().lower() == alvo.strip().lower():
                return ad["id"]
    raise SystemExit(f"Não achei nenhum anúncio com o nome \"{alvo}\".")


def modelo(alvo):
    if not alvo:
        raise SystemExit("Diga qual anúncio usar de modelo (nome ou id) no campo anuncio.")
    ad = chamar("GET", achar_anuncio(alvo), fields="id,name,account_id,campaign_id,adset_id,effective_status,creative{id}")
    criativo = chamar("GET", ad["creative"]["id"], fields=(
        "id,name,object_story_spec,asset_feed_spec,degrees_of_freedom_spec,url_tags,call_to_action_type,"
        "contextual_multi_ads,instagram_user_id,actor_id,object_type,status"))
    # Campos que só existem em alguns criativos (versão em pé, cortes): um por vez, pra um campo ausente não derrubar o resto.
    for campo in ("asset_feed_spec", "portrait_customizations", "platform_customizations", "image_crops",
                  "creative_sourcing_spec", "image_hash", "thumbnail_url"):
        if campo not in criativo:
            try:
                valor = chamar("GET", criativo["id"], fields=campo).get(campo)
            except SystemExit as e:
                valor = f"(erro: {e})"
            if valor is not None:
                criativo[campo] = valor
    conjunto = chamar("GET", ad["adset_id"], fields=(
        "id,name,daily_budget,lifetime_budget,optimization_goal,billing_event,bid_strategy,destination_type,"
        "promoted_object,attribution_spec,targeting,start_time,end_time,effective_status"))
    campanha = chamar("GET", ad["campaign_id"], fields=(
        "id,name,objective,special_ad_categories,special_ad_category_country,buying_type,effective_status"))
    dados = {"anuncio": ad, "criativo": criativo, "conjunto": conjunto, "campanha": campanha}
    with open(MODELO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(dados, ensure_ascii=False, indent=2))
    resumo(f"### Modelo gravado: {ad['name']}\n\nCampanha {campanha['name']}, conjunto {conjunto['name']}.")


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


# A Meta não aceita mais o pacote "melhorias padrão": cada melhoria com IA vai desligada, uma por uma,
# pra arte e o texto saírem exatamente como foram aprovados.
MELHORIAS_DESLIGADAS = ("image_touchups", "image_brightness_and_contrast", "image_uncrop", "image_templates",
                        "text_optimizations", "enhance_cta", "adapt_to_placement", "site_extensions",
                        "product_browsing")


def enviar_imagem(conta, arquivo):
    with open(os.path.join(ARTES, arquivo), "rb") as f:
        dados = base64.b64encode(f.read()).decode()
    imagens = chamar("POST", f"{conta}/adimages", bytes=dados, name=arquivo)["images"]
    return next(iter(imagens.values()))["hash"]


def especificacao(arte, link, plano, feed, vertical):
    """Uma arte em duas versões: a em pé (9:16) nos Stories e Reels, a normal em todo o resto."""
    return {
        "images": [{"hash": feed, "adlabels": [{"name": "feed"}]}, {"hash": vertical, "adlabels": [{"name": "vertical"}]}],
        "bodies": [{"text": arte["texto"]}],
        "titles": [{"text": arte["titulo"]}],
        "descriptions": [{"text": plano["descricao"]}],
        "link_urls": [{"website_url": link, "display_url": plano["link_de_exibicao"]}],
        "call_to_action_types": ["LEARN_MORE"],
        "ad_formats": ["SINGLE_IMAGE"],
        "optimization_type": "PLACEMENT",
        "asset_customization_rules": [
            {"customization_spec": {"publisher_platforms": ["facebook", "instagram", "messenger"],
                                    "facebook_positions": ["story", "facebook_reels"],
                                    "instagram_positions": ["story", "reels"],
                                    "messenger_positions": ["story"]},
             "image_label": {"name": "vertical"}, "priority": 1},
            {"customization_spec": {"publisher_platforms": ["facebook", "instagram", "messenger"]},
             "image_label": {"name": "feed"}, "priority": 2},
        ],
    }


def criar(limite):
    plano = carregar(PLANO, None)
    modelo = carregar(MODELO, None)
    if not plano or not modelo:
        raise SystemExit("Faltam anuncios/plano.json ou anuncios/modelo.json (rode o modo modelo antes).")
    criados = carregar(CRIADOS, {})
    base = chamar("GET", plano["modelo_conjunto"], fields="id,name,account_id,optimization_goal,daily_budget")
    conta = f"act_{base['account_id']}"
    historia = modelo["criativo"]["object_story_spec"]
    identidade = {"page_id": historia["page_id"], "instagram_user_id": historia.get("instagram_user_id")}
    melhorias = {"creative_features_spec": {nome: {"enroll_status": "OPT_OUT"} for nome in MELHORIAS_DESLIGADAS}}
    feitos = 0
    linhas = ["### Anúncios criados (pausados)", ""]

    existentes = {c["name"]: c for c in listar(f"{plano['campanha']}/adsets", fields="id,name,optimization_goal,daily_budget")}
    for cj in plano["conjuntos"]:
        atual = existentes.get(cj["nome"])
        if not atual:
            copia = chamar("POST", f"{base['id']}/copies", deep_copy="false", status_option="PAUSED")
            novo = copia.get("copied_adset_id") or copia.get("ad_object_ids", [{}])[0].get("copied_id")
            atual = chamar("GET", novo, fields="id,name,optimization_goal,daily_budget")
            print(f"Conjunto copiado do modelo: {cj['nome']} ({novo}), pausado")
        mudar = {}
        if atual["name"] != cj["nome"]:
            mudar["name"] = cj["nome"]
        e_modelo = atual["id"] == base["id"]
        if not e_modelo or plano.get("ajustar_conjunto_modelo"):
            if int(atual.get("daily_budget") or 0) != round(cj["orcamento_dia"] * 100):
                mudar["daily_budget"] = round(cj["orcamento_dia"] * 100)
            if atual.get("optimization_goal") != plano["meta_de_desempenho"]:
                mudar["optimization_goal"] = plano["meta_de_desempenho"]
        if mudar:
            chamar("POST", atual["id"], **mudar)
            print(f"Conjunto {cj['nome']}: ajustado {', '.join(mudar)}")
        criados.setdefault("conjuntos", {})[cj["nome"]] = atual["id"]
        salvar(CRIADOS, criados)

        anuncios = {a["name"] for a in listar(f"{atual['id']}/ads", fields="id,name")}
        link = f"https://ivanfulyconsorcios.com.br/?anuncio={cj['anuncio']}"
        for num in cj["artes"]:
            arte = plano["artes"][num]
            nome = f"{cj['nome']} - {arte['nome']}"
            if nome in anuncios:
                continue
            if limite and feitos >= limite:
                print(f"Parei no limite de {limite} anúncio(s) nesta rodada.")
                resumo("\n".join(linhas))
                return
            feed = enviar_imagem(conta, f"{arte['arquivo']}-FEED.jpg")
            vertical = enviar_imagem(conta, f"{arte['arquivo']}-STORIES.jpg")
            criativo = chamar("POST", f"{conta}/adcreatives", name=nome, object_story_spec=identidade,
                              asset_feed_spec=especificacao(arte, link, plano, feed, vertical),
                              degrees_of_freedom_spec=melhorias, contextual_multi_ads={"enroll_status": "OPT_OUT"})
            ad = chamar("POST", f"{conta}/ads", name=nome, adset_id=atual["id"],
                        creative={"creative_id": criativo["id"]}, status="PAUSED")
            criados.setdefault("anuncios", {})[nome] = {"id": ad["id"], "criativo": criativo["id"]}
            salvar(CRIADOS, criados)
            feitos += 1
            print(f"Criado (pausado): {nome} ({ad['id']})")
            time.sleep(10)
            linhas.append(f"- {nome}")
    print(f"Pronto: {feitos} anúncio(s) criado(s) nesta rodada.")
    resumo("\n".join(linhas + ["", f"{feitos} anúncio(s) criado(s), todos pausados."]))


def relatorio(periodo):
    preset = PERIODOS.get(periodo, "last_7d")
    linhas = [f"### Resultado dos anúncios ({periodo})", "",
              "| Conjunto | Anúncio | Gasto | Alcance | Cliques no link | CTR | Custo por clique |",
              "|---|---|---|---|---|---|---|"]
    total_gasto = total_cliques = 0.0
    for c in listar("me/adaccounts", fields="id"):
        dados = listar(f"{c['id']}/insights", level="ad", date_preset=preset, fields=(
            "campaign_name,adset_name,ad_name,spend,reach,impressions,frequency,inline_link_clicks,"
            "inline_link_click_ctr,cost_per_inline_link_click"))
        for d in sorted(dados, key=lambda d: (d.get("adset_name", ""), -float(d.get("inline_link_clicks") or 0))):
            gasto = float(d.get("spend") or 0)
            cliques = float(d.get("inline_link_clicks") or 0)
            total_gasto += gasto
            total_cliques += cliques
            cpc = brl(float(d["cost_per_inline_link_click"])) if d.get("cost_per_inline_link_click") else "-"
            ctr = f"{float(d['inline_link_click_ctr']):.2f}%".replace(".", ",") if d.get("inline_link_click_ctr") else "-"
            linha = (f"| {d.get('adset_name')} | {d.get('ad_name')} | {brl(gasto)} | {d.get('reach', 0)} | "
                     f"{int(cliques)} | {ctr} | {cpc} |")
            linhas.append(linha)
            print(linha)
    media = brl(total_gasto / total_cliques) if total_cliques else "-"
    fim = f"Total: {brl(total_gasto)} gastos, {int(total_cliques)} cliques no link, {media} por clique."
    print(fim)
    linhas += ["", fim]
    linhas += lugares(preset)
    resumo("\n".join(linhas))


# Onde a campanha do plano apareceu: clique barato em app de terceiros quase nunca vira conversa.
PLATAFORMAS = {"facebook": "Facebook", "instagram": "Instagram", "messenger": "Messenger",
               "audience_network": "Apps e sites parceiros (Audience Network)", "threads": "Threads"}


def lugares(preset):
    campanha = carregar(PLANO, {}).get("campanha")
    if not campanha:
        return []
    dados = listar(f"{campanha}/insights", date_preset=preset, breakdowns="publisher_platform,platform_position",
                   fields="spend,impressions,inline_link_clicks")
    linhas = ["", "### Onde os cliques aconteceram (campanha do plano)", "",
              "| Onde | Posição | Gasto | Impressões | Cliques no link | Custo por clique |", "|---|---|---|---|---|---|"]
    print("\nOnde os cliques aconteceram:")
    for d in sorted(dados, key=lambda d: -float(d.get("inline_link_clicks") or 0)):
        gasto = float(d.get("spend") or 0)
        cliques = int(float(d.get("inline_link_clicks") or 0))
        cpc = brl(gasto / cliques) if cliques else "-"
        linha = (f"| {PLATAFORMAS.get(d.get('publisher_platform'), d.get('publisher_platform'))} | "
                 f"{d.get('platform_position', '').replace('_', ' ')} | {brl(gasto)} | {d.get('impressions', 0)} | "
                 f"{cliques} | {cpc} |")
        linhas.append(linha)
        print(linha)
    return linhas


def main():
    global TOKEN
    TOKEN = os.environ.get("META_ADS_TOKEN", "").strip()
    if not TOKEN:
        raise SystemExit("Falta o segredo META_ADS_TOKEN no GitHub (Settings > Secrets and variables > Actions).")
    modo = os.environ.get("MODO", "verificar").strip() or "verificar"
    if modo == "verificar":
        verificar()
    elif modo == "modelo":
        modelo(os.environ.get("ANUNCIO", "").strip())
    elif modo == "criar":
        limite = os.environ.get("LIMITE", "").strip()
        criar(int(limite) if limite.isdigit() else 0)
    elif modo == "relatorio":
        relatorio(os.environ.get("PERIODO", "7dias").strip())
    else:
        raise SystemExit(f"Modo desconhecido: {modo}")


if __name__ == "__main__":
    main()
