#!/usr/bin/env python3
"""Robô dos anúncios: fala com a API de Marketing da Meta pelo GitHub.

Modos (variável MODO):
  verificar  mostra o que a chave enxerga: contas de anúncios, pixels, páginas, Instagram e campanhas
  modelo     mostra como a Meta guardou um anúncio feito à mão (variável ANUNCIO = nome ou id)
             e grava em anuncios/modelo.json, pra servir de molde pros próximos
  criar      cria a campanha, os conjuntos e os anúncios de anuncios/plano.json que ainda não existem, todos PAUSADOS
             (variável LIMITE = quantos anúncios no máximo nesta rodada; vazio = todos)
  ligar      liga a campanha do plano: os anúncios, os conjuntos e por último a campanha (só quando o Ivan pede)
  desligar   pausa todas as campanhas ligadas da conta (não exclui nada)
  excluir_criadas  exclui as campanhas do plano (a atual e a anterior); campanha feita à mão fica
  excluir_anterior  exclui a campanha anterior do plano (campanha_anterior), depois que a nova estiver ligada
  relatorio  gasto, alcance, cliques e custo por clique de cada anúncio, onde os cliques aconteceram
             (Instagram, Facebook, apps parceiros...) e o que o Pixel contou no site (variável PERIODO)

Nada aqui liga anúncio: o que o robô cria fica pausado até você ligar no Gerenciador.
E o robô nunca altera conjunto que está ligado: o que não serve se desliga, e o novo nasce do zero.
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
        for px in pixels(c):
            print(f"  {px}")
            linhas.append(f"  - {px}")
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


def pixels(conta):
    """Pixels (conjuntos de dados) que a conta de anúncios ou o portfólio dela enxergam."""
    achados = {}
    origens = [f"{conta['id']}/adspixels"]
    if conta.get("business"):
        origens.append(f"{conta['business']['id']}/adspixels")
    for origem in origens:
        try:
            for px in listar(origem, fields="id,name,creation_time,last_fired_time,is_unavailable"):
                achados.setdefault(px["id"], px)
        except SystemExit as e:
            print(f"  Não deu pra ler os pixels em {origem.split('/')[0]}: {e}")
    textos = []
    for px in achados.values():
        ultimo = (px.get("last_fired_time") or "nunca")[:10]
        criado = (px.get("creation_time") or "?")[:10]
        indisponivel = ", indisponível" if px.get("is_unavailable") else ""
        textos.append(f"Pixel: {px.get('name')} ({px['id']}), criado em {criado}, último disparo: {ultimo}{indisponivel}")
    return textos or ["Nenhum pixel encontrado pra esta conta."]


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


# Posições em pé (9:16) de cada plataforma.
VERTICAIS = {"facebook": ["story", "facebook_reels"], "instagram": ["story", "reels"], "messenger": ["story"]}


def especificacao(arte, link, plano, feed, vertical):
    """Uma arte em duas versões: a em pé (9:16) nos Stories e Reels, a normal em todo o resto."""
    lugares = plano.get("posicionamentos") or {}
    plataformas = lugares.get("publisher_platforms") or list(VERTICAIS)
    em_pe = {}
    for p in plataformas:
        escolhidas = lugares.get(f"{p}_positions")
        posicoes = [x for x in VERTICAIS.get(p, []) if escolhidas is None or x in escolhidas]
        if posicoes:
            em_pe[f"{p}_positions"] = posicoes
    em_pe = {"publisher_platforms": [p for p in plataformas if f"{p}_positions" in em_pe], **em_pe}
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
            {"customization_spec": em_pe, "image_label": {"name": "vertical"}, "priority": 1},
            {"customization_spec": {"publisher_platforms": plataformas}, "image_label": {"name": "feed"}, "priority": 2},
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

    if not plano.get("campanha"):
        origem = modelo["campanha"]
        campanha = chamar("POST", f"{conta}/campaigns", name=plano["nome_da_campanha"], objective=origem["objective"],
                          buying_type=origem.get("buying_type", "AUCTION"), status="PAUSED",
                          special_ad_categories=origem.get("special_ad_categories", []),
                          special_ad_category_country=origem.get("special_ad_category_country", []),
                          is_adset_budget_sharing_enabled="false")
        plano["campanha"] = campanha["id"]
        salvar(PLANO, plano)
        print(f"Campanha criada (pausada): {plano['nome_da_campanha']} ({campanha['id']})")
        linhas += [f"Campanha nova (pausada): **{plano['nome_da_campanha']}**", ""]

    campos = "id,name,optimization_goal,daily_budget,effective_status"
    existentes = {c["name"]: c for c in listar(f"{plano['campanha']}/adsets", fields=campos)}
    # Cópia que ficou pela metade numa rodada que deu erro (ainda com o nome "... - Cópia"): reaproveita.
    sobras = [c for nome, c in existentes.items() if nome not in {cj["nome"] for cj in plano["conjuntos"]}
              and ("Cópia" in nome or "Copy" in nome) and c.get("effective_status") != "ACTIVE"]
    for cj in plano["conjuntos"]:
        atual = existentes.get(cj["nome"]) or (sobras.pop(0) if sobras else None)
        if atual and atual.get("effective_status") == "ACTIVE":
            print(f"Conjunto {cj['nome']} está ligado: não mexo nele (o que não serve se desliga, e o novo nasce do zero).")
            linhas.append(f"- {cj['nome']}: ligado, não mexi")
            continue
        if not atual:
            copia = chamar("POST", f"{base['id']}/copies", campaign_id=plano["campanha"], deep_copy="false",
                           status_option="PAUSED")
            novo = copia.get("copied_adset_id") or copia.get("ad_object_ids", [{}])[0].get("copied_id")
            atual = chamar("GET", novo, fields=campos)
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
            if plano.get("posicionamentos"):
                alvo = chamar("GET", atual["id"], fields="targeting")["targeting"]
                if any(alvo.get(k) != v for k, v in plano["posicionamentos"].items()):
                    alvo.update(plano["posicionamentos"])
                    if "audience_network" not in alvo["publisher_platforms"] and alvo.get("brand_safety_content_filter_levels"):
                        alvo["brand_safety_content_filter_levels"] = [
                            n for n in alvo["brand_safety_content_filter_levels"] if not n.startswith("AN_")]
                    mudar["targeting"] = alvo
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


def ligar():
    """Liga a campanha do plano. Os anúncios e conjuntos primeiro, a campanha por último, pra tudo começar junto."""
    plano = carregar(PLANO, {})
    if not plano.get("campanha"):
        raise SystemExit("Não há campanha no plano (rode o modo criar antes).")
    camp = chamar("GET", plano["campanha"], fields="id,name,status")
    linhas = [f"### Ligando a campanha {camp['name']}", ""]
    for cj in listar(f"{camp['id']}/adsets", fields="id,name,status"):
        for ad in listar(f"{cj['id']}/ads", fields="id,name,status"):
            if ad["status"] != "ACTIVE":
                chamar("POST", ad["id"], status="ACTIVE")
            print(f"Anúncio ligado: {ad['name']}")
            linhas.append(f"- Anúncio ligado: {ad['name']}")
        if cj["status"] != "ACTIVE":
            chamar("POST", cj["id"], status="ACTIVE")
        print(f"Conjunto ligado: {cj['name']}")
        linhas.append(f"- Conjunto ligado: **{cj['name']}**")
    if camp["status"] != "ACTIVE":
        chamar("POST", camp["id"], status="ACTIVE")
    print(f"Campanha ligada: {camp['name']} ({camp['id']})")
    resumo("\n".join(linhas + ["", f"Campanha ligada: **{camp['name']}**"]))


def desligar():
    """Pausa todas as campanhas ligadas da conta. Nada é excluído, e dá pra religar depois."""
    linhas = ["### Campanhas desligadas", ""]
    for c in listar("me/adaccounts", fields="id"):
        for camp in listar(f"{c['id']}/campaigns", fields="id,name,status"):
            if camp["status"] == "ACTIVE":
                chamar("POST", camp["id"], status="PAUSED")
                print(f"Campanha desligada: {camp['name']} ({camp['id']})")
                linhas.append(f"- Desligada: **{camp['name']}**")
            else:
                print(f"Já estava desligada: {camp['name']} ({camp['status']})")
    resumo("\n".join(linhas))


def excluir_criadas():
    """Exclui só as campanhas do plano (campanha e campanha_anterior). Qualquer outra campanha da conta fica como está."""
    plano = carregar(PLANO, {})
    linhas = ["### Campanhas excluídas", ""]
    for camp_id in dict.fromkeys(c for c in (plano.get("campanha"), plano.get("campanha_anterior")) if c):
        camp = chamar("GET", camp_id, fields="id,name,status")
        if camp["status"] == "DELETED":
            print(f"Já estava excluída: {camp['name']} ({camp_id})")
            continue
        chamar("POST", camp_id, status="DELETED")
        print(f"Campanha excluída: {camp['name']} ({camp_id})")
        linhas.append(f"- Excluída: **{camp['name']}**")
    resumo("\n".join(linhas))


def excluir_anterior():
    """Exclui a campanha anterior, só se a nova já estiver ligada (pra nunca ficar sem anúncio rodando)."""
    plano = carregar(PLANO, {})
    antiga, nova = plano.get("campanha_anterior"), plano.get("campanha")
    if not antiga or antiga == nova:
        raise SystemExit("Não há campanha anterior no plano.")
    if not nova or chamar("GET", nova, fields="status")["status"] != "ACTIVE":
        raise SystemExit("A campanha nova ainda não está ligada. Ligue a nova antes de excluir a anterior.")
    velha = chamar("GET", antiga, fields="id,name,status")
    if velha["status"] != "DELETED":
        chamar("POST", antiga, status="DELETED")
    print(f"Campanha excluída: {velha['name']} ({antiga})")
    resumo(f"Campanha excluída: **{velha['name']}**")


# Anúncio excluído continua contando no relatório (gasto e cliques que já aconteceram).
TODOS_OS_STATUS = ["ACTIVE", "PAUSED", "DELETED", "ARCHIVED", "PENDING_REVIEW", "DISAPPROVED", "PREAPPROVED",
                   "PENDING_BILLING_INFO", "CAMPAIGN_PAUSED", "ADSET_PAUSED", "IN_PROCESS", "WITH_ISSUES"]


def relatorio(periodo):
    preset = PERIODOS.get(periodo, "last_7d")
    linhas = [f"### Resultado dos anúncios ({periodo})", "",
              "| Conjunto | Anúncio | Gasto | Alcance | Cliques no link | CTR | Custo por clique |",
              "|---|---|---|---|---|---|---|"]
    total_gasto = total_cliques = 0.0
    for c in listar("me/adaccounts", fields="id"):
        dados = listar(f"{c['id']}/insights", level="ad", date_preset=preset,
                       filtering=[{"field": "ad.effective_status", "operator": "IN", "value": TODOS_OS_STATUS}], fields=(
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
    linhas += eventos_do_pixel(preset)
    resumo("\n".join(linhas))


# Onde a campanha do plano apareceu: clique barato em app de terceiros quase nunca vira conversa.
PLATAFORMAS = {"facebook": "Facebook", "instagram": "Instagram", "messenger": "Messenger",
               "audience_network": "Apps e sites parceiros (Audience Network)", "threads": "Threads"}


EVENTOS = {"PageView": "Visitas ao site", "Contact": "Toques no botão do WhatsApp"}


def eventos_do_pixel(preset):
    """Quantas visitas e toques no WhatsApp o Pixel contou (só de quem tocou em "Pode" no aviso de cookies)."""
    pixel = carregar(PLANO, {}).get("pixel")
    if not pixel:
        return []
    agora = int(time.time())
    hoje = agora - (agora - 3 * 3600) % 86400  # meia-noite no horário de Brasília
    inicio, fim = {"today": (hoje, agora), "yesterday": (hoje - 86400, hoje), "last_7d": (hoje - 7 * 86400, hoje),
                   "last_30d": (hoje - 30 * 86400, hoje)}.get(preset, (agora - 90 * 86400, agora))
    print("\nO que o Pixel contou no site:")
    try:
        blocos = listar(f"{pixel}/stats", aggregation="event", start_time=inicio, end_time=fim)
    except SystemExit as e:
        print(f"Não deu pra ler o pixel: {e}")
        return ["", f"Não deu pra ler o pixel: {e}"]
    contagem = {}
    for bloco in blocos:
        for item in bloco.get("data", []):
            contagem[item.get("value")] = contagem.get(item.get("value"), 0) + int(item.get("count") or 0)
    linhas = ["", "### O que o Pixel contou no site", "",
              "Só conta quem tocou em \"Pode\" no aviso de cookies.", ""]
    for evento, nome in EVENTOS.items():
        linha = f"- {nome}: {contagem.pop(evento, 0)}"
        linhas.append(linha)
        print(linha)
    for evento, total in contagem.items():
        linha = f"- {evento}: {total}"
        linhas.append(linha)
        print(linha)
    return linhas


def lugares(preset):
    plano = carregar(PLANO, {})
    linhas = []
    for campanha, qual in ((plano.get("campanha"), "campanha atual"), (plano.get("campanha_anterior"), "campanha anterior")):
        if campanha:
            linhas += lugares_da_campanha(campanha, qual, preset)
    return linhas


def lugares_da_campanha(campanha, qual, preset):
    dados = listar(f"{campanha}/insights", date_preset=preset, breakdowns="publisher_platform,platform_position",
                   fields="spend,impressions,inline_link_clicks")
    if not dados:
        return []
    linhas = ["", f"### Onde os cliques aconteceram ({qual})", "",
              "| Onde | Posição | Gasto | Impressões | Cliques no link | Custo por clique |", "|---|---|---|---|---|---|"]
    print(f"\nOnde os cliques aconteceram ({qual}):")
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
    elif modo == "ligar":
        ligar()
    elif modo == "desligar":
        desligar()
    elif modo == "excluir_criadas":
        excluir_criadas()
    elif modo == "excluir_anterior":
        excluir_anterior()
    elif modo == "relatorio":
        relatorio(os.environ.get("PERIODO", "7dias").strip())
    else:
        raise SystemExit(f"Modo desconhecido: {modo}")


if __name__ == "__main__":
    main()
