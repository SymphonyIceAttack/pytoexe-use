# -*- coding: utf-8 -*-
"""
MINERADOR DE CANAIS DO YOUTUBE
------------------------------------------------------------------
Abre uma janela onde voce escolhe os filtros e digita as palavras-chave.
O programa pesquisa no YouTube e devolve SO os canais que batem suas regras.

NOVIDADES desta versao:
  - Varias chaves de API (uma por linha). Quando uma esgota a cota do dia,
    ele pula sozinho pra proxima.
  - Som de aviso ("plin") quando a pesquisa termina (usa um som do proprio
    Windows; nao precisa de arquivo nenhum).
  - Se a cota de TODAS as chaves acabar no meio, ele NAO descarta tudo:
    entrega os canais que ja conseguiu coletar ate ali, marcando com "—" o
    que nao deu pra checar por falta de cota.
  - MEMORIA entre rodadas: a data do 1o video de cada canal fica salva, entao
    ele nao gasta cota investigando de novo um canal ja visto (economia grande
    pra quem roda todo dia).
  - Marca ✨ NOVIDADE nos canais que nunca apareceram antes, com botao pra
    mostrar so as novidades (escondendo os que voce ja viu).
  - Botao PARAR: encerra a busca na hora e entrega o que ja coletou.
  - Filtro de idioma na busca (PT, FR, EN, ES ou todos).
  - Tenta de novo sozinho se a internet cair no meio de uma rodada.
  - Ordenar resultados (mais views / 1o video mais recente / etc).
  - Filtro de duracao na busca + corte fino em minutos (mata Shorts).

So precisa de Python instalado. Nao precisa instalar mais nada.
------------------------------------------------------------------
"""

import json
import csv
import os
import re
import threading
import queue
import webbrowser
import time
from datetime import datetime, timedelta, timezone
from urllib import request, parse, error

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ============================================================
# Suas chaves vao na propria janela (uma por linha) e ficam
# salvas no arquivo chaves_api.txt ao lado deste .py.
# ============================================================
API_BASE = "https://www.googleapis.com/youtube/v3"
ARQ_CHAVES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chaves_api.txt")
# Memoria entre rodadas: guarda, por canal, a data do 1o video (que nunca muda,
# entao nao precisa gastar cota investigando de novo) e se o canal ja apareceu
# em alguma busca anterior (pra marcar "novidade" vs "ja visto").
ARQ_MEMORIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memoria_canais.json")


# ------------------------------------------------------------
# CHAVES DE API SALVAS EM ARQUIVO (uma por linha)
# ------------------------------------------------------------
def carregar_chaves():
    """Le chaves_api.txt e devolve uma lista (sem duplicatas, sem linhas vazias)."""
    try:
        with open(ARQ_CHAVES, encoding="utf-8") as f:
            brutas = f.read().splitlines()
    except FileNotFoundError:
        return []
    except Exception:
        return []
    out, vistas = [], set()
    for l in brutas:
        k = l.strip()
        if k and k not in vistas:
            vistas.add(k); out.append(k)
    return out


def salvar_chaves(chaves):
    """Grava a lista de chaves em chaves_api.txt (uma por linha)."""
    try:
        with open(ARQ_CHAVES, "w", encoding="utf-8") as f:
            f.write("\n".join(chaves))
    except Exception:
        pass


# ------------------------------------------------------------
# MEMORIA DOS CANAIS (entre rodadas) — economiza cota e marca novidades
# ------------------------------------------------------------
def carregar_memoria():
    """Le memoria_canais.json. Devolve um dict {channelId: {...}}.
    Cada canal pode ter:
      - 'primeiro_video': data ISO do 1o video (cache; nunca muda)
      - 'ja_apareceu'   : True se o canal ja saiu em alguma busca anterior
    Se o arquivo nao existir ou estiver corrompido, devolve {} (comeca do zero)."""
    try:
        with open(ARQ_MEMORIA, encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict):
            return {}
        return {k: v for k, v in d.items() if isinstance(v, dict)}
    except Exception:
        return {}


def salvar_memoria(mem):
    """Grava a memoria dos canais em memoria_canais.json."""
    try:
        with open(ARQ_MEMORIA, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False)
    except Exception:
        pass


# ------------------------------------------------------------
# ROTULO CURTO DA CHAVE (so pra aparecer nas mensagens de erro)
# ------------------------------------------------------------
def _label_chave(k):
    return "..." + k[-6:] if len(k) >= 6 else k


# ------------------------------------------------------------
# GERENCIADOR DE CHAVES (faz o rodizio automatico)
# ------------------------------------------------------------
class ApiError(Exception):
    def __init__(self, msg, reason=""):
        super().__init__(msg)
        self.reason = reason


class CotaEsgotada(ApiError):
    """Todas as chaves esgotaram a cota do dia.
    NAO e um erro fatal: o programa entrega o que ja tiver coletado ate aqui,
    em vez de derrubar a pesquisa inteira."""
    pass


class KeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.i = 0
        self.esgotadas = set()
        self.cota_esgotada = False   # vira True quando TODAS as chaves esgotam a cota do dia
        self.cancelado = False       # vira True quando o usuario aperta "Parar"

    def atual(self):
        # Pula as chaves que já esgotaram a cota diária
        inicio = self.i
        while self.i in self.esgotadas:
            self.i = (self.i + 1) % len(self.keys)
            if self.i == inicio:
                break
        return self.keys[self.i]

    def rodiziar(self):
        """Pula para a proxima chave depois de cada chamada (espalha o uso)."""
        self.i = (self.i + 1) % len(self.keys)

    def avancar(self):
        """Marca a chave atual como esgotada e tenta ir pra próxima.
        Devolve False quando ja nao sobra nenhuma chave com cota
        (e nesse caso liga o sinal cota_esgotada)."""
        self.esgotadas.add(self.i)
        if len(self.esgotadas) < len(self.keys):
            self.i = (self.i + 1) % len(self.keys)
            return True
        self.cota_esgotada = True
        return False


# ------------------------------------------------------------
# CONVERSA COM O YOUTUBE
# ------------------------------------------------------------
def api_get(endpoint, params, km, _max_retries_rede=3):
    # Se a cota de TODAS as chaves ja acabou, nem tenta a rede: avisa quem chamou
    # pra ele entregar o que ja tem.
    if km.cota_esgotada:
        raise CotaEsgotada("Cota diaria esgotada em todas as chaves.")
    rede_falhas = 0   # quedas de conexao seguidas (pra tentar de novo antes de desistir)
    while True:
        chave = km.atual()
        p = dict(params)
        p["key"] = chave
        url = API_BASE + "/" + endpoint + "?" + parse.urlencode(p)
        req = request.Request(url, headers={"User-Agent": "MineradorYT/1.0"})
        try:
            with request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            km.rodiziar()

            # DELAY PADRÃO: Espera meio segundo entre as requisições para evitar rate limit
            time.sleep(0.5)

            return data
        except error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            reason, msg = "", body
            try:
                j = json.loads(body)
                errs = j.get("error", {}).get("errors", [{}])
                reason = errs[0].get("reason", "")
                msg = j.get("error", {}).get("message", "")
            except Exception:
                pass

            # Excesso de requisições por minuto
            if reason == "rateLimitExceeded":
                time.sleep(2)  # deixa a API do Google "respirar"
                if km.avancar():
                    continue   # tenta novamente com a próxima chave
                raise ApiError(
                    "O Google bloqueou as buscas temporariamente (muitas requisições por minuto). "
                    "Tente buscar menos páginas por vez."
                )

            # Esgotamento da cota diária (10.000 por chave)
            if reason == "quotaExceeded":
                if km.avancar():
                    continue   # tenta a MESMA chamada com a próxima chave
                # Acabou a cota de TODAS as chaves. Em vez de derrubar a busca,
                # sinaliza com CotaEsgotada: o motor entrega o que ja coletou.
                raise CotaEsgotada("Cota diaria esgotada em todas as chaves.")

            if reason in ("badRequest", "keyInvalid"):
                raise ApiError(
                    "A chave %s parece inválida. Confira se copiou certo e se ativou "
                    "a 'YouTube Data API v3' no projeto dela." % _label_chave(chave)
                )
            raise ApiError("Erro da API (%s): %s" % (reason or "desconhecido", msg), reason=reason)
        except error.URLError as e:
            # Queda de internet / DNS / timeout: tenta de novo umas vezes antes de
            # desistir (a mesma chamada, sem gastar nem trocar de chave). Espera
            # crescente entre as tentativas (2s, 4s, 6s).
            rede_falhas += 1
            if rede_falhas <= _max_retries_rede:
                time.sleep(2 * rede_falhas)
                continue
            raise ApiError("Sem conexão com a internet? Detalhe técnico: %s" % e)


def iso_dias_atras(dias):
    dt = datetime.now(timezone.utc) - timedelta(days=dias)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def fmt(n):
    return ("{:,}".format(int(n))).replace(",", ".")


def _txt(v):
    """Como mostrar um campo na tabela: numero formatado, texto, ou '—'
    quando o dado e desconhecido (None) porque a cota acabou antes de checar."""
    if v is None:
        return "—"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        return fmt(v)
    return str(v)


def tocar_som(tipo="ok"):
    """Toca um som do proprio Windows (nao precisa de arquivo nenhum).
       'ok'   -> bipe suave de aviso (o "plin" de fim de pesquisa).
       'erro' -> som de erro do Windows.
    Em outros sistemas (ou se nao rolar), tenta o bipe do terminal e segue
    sem travar a janela."""
    try:
        import winsound
        if tipo == "erro":
            winsound.MessageBeep(winsound.MB_ICONHAND)
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        try:
            print("\a", end="", flush=True)
        except Exception:
            pass


def duracao_para_segundos(iso):
    if not iso:
        return 0
    m = re.match(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mi = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + mi * 60 + s


def segundos_para_texto(seg):
    seg = int(seg)
    h, resto = divmod(seg, 3600)
    m, s = divmod(resto, 60)
    if h:
        return "%d:%02d:%02d" % (h, m, s)
    return "%d:%02d" % (m, s)


# Limite de views (no periodo da busca) que define um video "em alta" pra fins do icone.
LIMITE_VIEWS_ICONE = 10000


def icone_canal(stats):
    """Devolve um emoji baseado em quantos videos do canal apareceram na busca
    com +10k views no periodo. Regras:
      - 1 ou 2 videos com +10k views ............ 👀
      - 3 ou mais videos com +10k views ......... 💎
      - 3+ videos E TODOS com +10k views ........ 💀  (substitui o diamante)
    """
    if not stats:
        return ""
    alta = stats["alta"]
    total = stats["total"]
    if alta >= 3 and alta == total:
        return "💀"
    if alta >= 3:
        return "💎"
    if alta >= 1:   # 1 ou 2
        return "👀"
    return ""


def ordenar_resultados(lista, modo):
    """Ordena os resultados. Itens cujo campo de ordenacao e desconhecido
    (None, porque a cota acabou antes de checar) vao sempre pro FIM da lista."""
    campo, reverso = {
        "1o video mais recente": ("Idade do canal (dias)", False),
        "1o video mais antigo":  ("Idade do canal (dias)", True),
        "Mais inscritos":        ("Inscritos", True),
    }.get(modo, ("Views do video", True))   # padrao: Mais views
    com = [r for r in lista if r.get(campo) is not None]
    sem = [r for r in lista if r.get(campo) is None]
    com.sort(key=lambda r: r[campo], reverse=reverso)
    return com + sem


# ------------------------------------------------------------
# EXTRACAO DE TAGS
# ------------------------------------------------------------
def extrair_tags_dos_videos(video_ids, km):
    """Busca as tags de uma lista de video IDs via API e devolve uma lista
    unica (sem repeticoes, case-insensitive), na ordem em que apareceram."""
    todas = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        try:
            data = api_get("videos", {"part": "snippet", "id": ",".join(chunk)}, km)
        except CotaEsgotada:
            break   # acabou a cota: devolve as tags que ja deu pra pegar
        for item in data.get("items", []):
            tags = item.get("snippet", {}).get("tags") or []
            todas.extend(tags)
    vistas = set()
    unicas = []
    for t in todas:
        tl = t.lower()
        if tl not in vistas:
            vistas.add(tl)
            unicas.append(t)
    return unicas


# ------------------------------------------------------------
# BUSCA E COLETA
# ------------------------------------------------------------
def buscar_videos(kw, dias, paginas, km, video_duration="any", idioma=""):
    publicado_apos = iso_dias_atras(dias)
    ids = []
    page_token = None
    for _ in range(paginas):
        if km.cancelado:
            break   # usuario apertou "Parar": devolve o que ja achou
        params = {
            "part": "snippet", "type": "video", "order": "viewCount",
            "maxResults": 50, "q": kw, "publishedAfter": publicado_apos,
        }
        if video_duration and video_duration != "any":
            params["videoDuration"] = video_duration
        if idioma:
            # "relevanceLanguage" puxa os resultados pro idioma escolhido
            # (e uma preferencia, nao um filtro 100% rigido).
            params["relevanceLanguage"] = idioma
        if page_token:
            params["pageToken"] = page_token
        try:
            data = api_get("search", params, km)
        except CotaEsgotada:
            break   # acabou a cota: devolve os videos que ja achou
        for item in data.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if vid:
                ids.append(vid)
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return ids


def stats_dos_videos(video_ids, km):
    out = {}
    for i in range(0, len(video_ids), 50):
        if km.cancelado:
            break   # usuario apertou "Parar": devolve as estatisticas que ja tem
        chunk = video_ids[i:i + 50]
        try:
            data = api_get("videos",
                           {"part": "statistics,snippet,contentDetails", "id": ",".join(chunk)}, km)
        except CotaEsgotada:
            break   # acabou a cota: devolve as estatisticas que ja coletou
        for item in data.get("items", []):
            st = item.get("statistics", {})
            dur = item.get("contentDetails", {}).get("duration", "")
            out[item["id"]] = {
                "views": int(st.get("viewCount", 0)),
                "title": item["snippet"]["title"],
                "channelId": item["snippet"]["channelId"],
                "channelTitle": item["snippet"]["channelTitle"],
                "dur_seg": duracao_para_segundos(dur),
            }
    return out


def info_dos_canais(channel_ids, km):
    out = {}
    ids = list(channel_ids)
    for i in range(0, len(ids), 50):
        if km.cancelado:
            break   # usuario apertou "Parar": devolve a info que ja tem
        chunk = ids[i:i + 50]
        try:
            data = api_get("channels",
                           {"part": "statistics,contentDetails,snippet", "id": ",".join(chunk)}, km)
        except CotaEsgotada:
            break   # acabou a cota: devolve a info dos canais que ja deu pra checar
        for item in data.get("items", []):
            st = item.get("statistics", {})
            oculto = bool(st.get("hiddenSubscriberCount"))
            out[item["id"]] = {
                "title": item["snippet"]["title"],
                "subs": 0 if oculto else int(st.get("subscriberCount", 0)),
                "subsHidden": oculto,
                "videoCount": int(st.get("videoCount", 0)),
                "uploads": item["contentDetails"]["relatedPlaylists"].get("uploads"),
            }
    return out


def data_primeiro_video(uploads_playlist, total_videos, km, limite_paginas=8):
    if not uploads_playlist:
        return None
    if total_videos > limite_paginas * 50:
        return None   # video demais = claramente nao e novo
    mais_antigo = None
    page_token = None
    paginas = 0
    while True:
        params = {"part": "contentDetails", "playlistId": uploads_playlist, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        try:
            data = api_get("playlistItems", params, km)
        except CotaEsgotada:
            # Acabou a cota no meio: nao da pra terminar de investigar a idade.
            # Devolve None; quem chamou (rodar_mineracao) ve o sinal cota_esgotada
            # e decide entregar o canal mesmo assim, sem a idade.
            return None
        except ApiError as e:
            # Canais terminados/privados ou sem uploads expostos devolvem playlistNotFound.
            # Nao e fatal: so significa que nao da pra investigar a idade desse canal.
            # O caller (rodar_mineracao) ja pula canais que retornam None.
            if getattr(e, "reason", "") in ("playlistNotFound", "playlistItemsNotAccessible", "channelNotFound"):
                return None
            raise
        for item in data.get("items", []):
            pub = item.get("contentDetails", {}).get("videoPublishedAt")
            if pub and (mais_antigo is None or pub < mais_antigo):
                mais_antigo = pub
        page_token = data.get("nextPageToken")
        paginas += 1
        if not page_token or paginas >= limite_paginas:
            break
    return mais_antigo


# ------------------------------------------------------------
# MONTAGEM DE LINHA E PLANILHA (aguentam dado faltando)
# ------------------------------------------------------------
def _montar_linha(cid, binfo, videos_por_canal, ci=None, primeira=None, novo=True):
    """Monta uma linha de resultado com o que estiver disponivel.
       ci=None       -> nao deu pra checar inscritos (a cota acabou antes).
       primeira=None -> nao deu pra checar a idade do 1o video.
       novo=False    -> esse canal ja apareceu numa busca anterior (nao e novidade).
    Campos desconhecidos ficam como None (aparecem como '—' na tela e como
    'nao verificado' na planilha)."""
    subs = ci["subs"] if ci else None
    total_vids = ci["videoCount"] if ci else None
    nome = ci["title"] if ci else (binfo.get("channelTitle") or "(sem nome)")
    if primeira:
        prim_txt = parse_iso(primeira).strftime("%d/%m/%Y")
        idade = max((datetime.now(timezone.utc) - parse_iso(primeira)).days, 0)
    else:
        prim_txt = None
        idade = None
    return {
        "Icone": icone_canal(videos_por_canal.get(cid)),
        "Novidade": "novo" if novo else "visto",
        "Canal": nome,
        "Inscritos": subs,
        "Total de videos": total_vids,
        "1o video": prim_txt,
        "Idade do canal (dias)": idade,
        "Video em alta": binfo["title"],
        "Duracao": segundos_para_texto(binfo.get("dur_seg", 0)),
        "Views do video": binfo["views"],
        "Palavra-chave": binfo["keyword"],
        "Link do canal": "https://www.youtube.com/channel/" + cid,
        "Link do video": "https://www.youtube.com/watch?v=" + binfo["videoId"],
    }


def _salvar_csv(resultados):
    """Salva a planilha. Campos desconhecidos (None) viram 'nao verificado'."""
    if not resultados:
        return None
    nome = "canais_encontrados_%s.csv" % datetime.now().strftime("%Y-%m-%d_%H%M%S")
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), nome)
    campos = list(resultados[0].keys())
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        for r in resultados:
            w.writerow({k: ("nao verificado" if v is None else v) for k, v in r.items()})
    return caminho


# ------------------------------------------------------------
# O MOTOR
# ------------------------------------------------------------
def rodar_mineracao(cfg, q):
    try:
        km = cfg["km"]
        kws = cfg["keywords"]

        # Memoria entre rodadas: o que ja sabemos de antes.
        memoria = carregar_memoria()
        vistos_antes = {cid for cid, v in memoria.items() if v.get("ja_apareceu")}

        # ---- ETAPA 1: busca + estatisticas dos videos (uma palavra-chave por vez) ----
        todos_videos = {}
        for kw in kws:
            if km.cota_esgotada or km.cancelado:
                break
            q.put(("log", "Buscando: '%s'  (ultimos %d dias)..." % (kw, cfg["search_days"])))
            ids = buscar_videos(kw, cfg["search_days"], cfg["paginas"], km,
                                cfg.get("video_duration", "any"), cfg.get("idioma", ""))
            q.put(("log", "   %d videos encontrados na busca." % len(ids)))
            if ids:
                stats = stats_dos_videos(ids, km)
                for vid, info in stats.items():
                    info["keyword"] = kw
                    info["videoId"] = vid
                    if vid not in todos_videos or info["views"] > todos_videos[vid]["views"]:
                        todos_videos[vid] = info

        if km.cota_esgotada:
            q.put(("log", "\n⚠️  A cota de TODAS as chaves acabou no meio da busca."))
            q.put(("log", "    Vou trabalhar com o que ja consegui ate aqui (nada e descartado)."))
        elif km.cancelado:
            q.put(("log", "\n⏹️  Busca interrompida. Vou entregar o que ja consegui ate aqui."))

        # Conta, por canal, quantos videos da busca tem +10k views (define o icone).
        videos_por_canal = {}
        for _vid, _info in todos_videos.items():
            _cid = _info["channelId"]
            slot = videos_por_canal.setdefault(_cid, {"total": 0, "alta": 0})
            slot["total"] += 1
            if _info["views"] >= LIMITE_VIEWS_ICONE:
                slot["alta"] += 1

        # ---- FILTRO 1: duracao + views (dados locais, sempre da pra aplicar) ----
        min_dur = cfg["min_dur_seg"]
        max_dur = cfg["max_dur_seg"]
        descartados_dur = 0
        melhor_por_canal = {}
        for vid, info in todos_videos.items():
            if info.get("dur_seg", 0) < min_dur:
                descartados_dur += 1
                continue
            if max_dur and info.get("dur_seg", 0) > max_dur:
                descartados_dur += 1
                continue
            if info["views"] >= cfg["min_views"]:
                cid = info["channelId"]
                if cid not in melhor_por_canal or info["views"] > melhor_por_canal[cid]["views"]:
                    melhor_por_canal[cid] = info
        if descartados_dur:
            q.put(("log", "   (%d videos cortados por duracao, ex.: Shorts)" % descartados_dur))
        q.put(("log", "\n-> %d canais com video de +%s views no periodo."
                      % (len(melhor_por_canal), fmt(cfg["min_views"]))))

        parar_api = km.cota_esgotada or km.cancelado

        if not melhor_por_canal:
            q.put(("done", {"results": [], "csv": None,
                            "parcial": parar_api, "cancelado": km.cancelado}))
            return

        # ---- FILTRO 2: inscritos (precisa de API) ----
        canais = {}
        if not (km.cota_esgotada or km.cancelado):
            canais = info_dos_canais(melhor_por_canal.keys(), km)

        sobreviventes = []   # (cid, binfo, ci)  -> inscritos checados e aprovados
        sem_info = []        # (cid, binfo)      -> nao deu pra checar inscritos (cota/parada)
        for cid, binfo in melhor_por_canal.items():
            ci = canais.get(cid)
            if ci is None:
                sem_info.append((cid, binfo))
                continue
            if ci["subsHidden"]:
                continue
            if ci["subs"] >= cfg["min_subs"]:
                sobreviventes.append((cid, binfo, ci))
        q.put(("log", "-> %d desses tem +%s inscritos." % (len(sobreviventes), fmt(cfg["min_subs"]))))

        # ---- FILTRO 3: idade do 1o video ----
        # A data do 1o video NUNCA muda, entao reaproveitamos da memoria (cache):
        # canal ja investigado antes nao gasta cota de novo. So canais ineditos
        # (ou ainda nao cacheados) batem na API.
        resultados = []
        cids_no_resultado = set()
        for cid, binfo, ci in sobreviventes:
            primeira = (memoria.get(cid) or {}).get("primeiro_video")   # cache (ISO) ou None
            if not primeira and not (km.cota_esgotada or km.cancelado):
                q.put(("log", "   Investigando canal: %s ..." % ci["title"]))
                primeira = data_primeiro_video(ci["uploads"], ci["videoCount"], km)
                if primeira:
                    memoria.setdefault(cid, {})["primeiro_video"] = primeira   # guarda pro futuro
            if primeira:
                idade = max((datetime.now(timezone.utc) - parse_iso(primeira)).days, 0)
                if idade <= cfg["max_first_age"]:
                    resultados.append(_montar_linha(cid, binfo, videos_por_canal,
                                                    ci=ci, primeira=primeira,
                                                    novo=(cid not in vistos_antes)))
                    cids_no_resultado.add(cid)
            else:
                # Sem data: se foi cota/parada, entrega o canal mesmo assim (sem a idade).
                # Senao (canal grande demais/privado/sem uploads), pula como antes.
                if km.cota_esgotada or km.cancelado:
                    resultados.append(_montar_linha(cid, binfo, videos_por_canal,
                                                    ci=ci, primeira=None,
                                                    novo=(cid not in vistos_antes)))
                    cids_no_resultado.add(cid)

        # Canais cujos inscritos nao deram pra checar (cota/parada na ETAPA 2):
        # entram mesmo assim, marcados como nao verificados.
        for cid, binfo in sem_info:
            resultados.append(_montar_linha(cid, binfo, videos_por_canal,
                                            ci=None, primeira=None,
                                            novo=(cid not in vistos_antes)))
            cids_no_resultado.add(cid)

        # Atualiza a memoria: marca os canais que apareceram nesta rodada e
        # salva (inclui as datas de 1o video recem-descobertas).
        for cid in cids_no_resultado:
            memoria.setdefault(cid, {})["ja_apareceu"] = True
        salvar_memoria(memoria)

        resultados = ordenar_resultados(resultados, cfg.get("ordenar", "Mais views"))
        caminho = _salvar_csv(resultados)

        for r in resultados:
            q.put(("row", r))
        q.put(("done", {"results": resultados, "csv": caminho,
                        "parcial": (km.cota_esgotada or km.cancelado),
                        "cancelado": km.cancelado}))

    except ApiError as e:
        q.put(("error", str(e)))
    except Exception as e:
        q.put(("error", "Erro inesperado: %s" % e))


# ------------------------------------------------------------
# A JANELA
# ------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Minerador de Canais do YouTube")
        self.geometry("1000x780")
        self.minsize(860, 640)
        self.q = queue.Queue()
        self.ultimo_csv = None
        self.resultados = []
        self.km = None   # guardado para reusar na extracao de tags
        self.so_novos = False   # filtro "mostrar so novidades" (liga/desliga apos a busca)
        self._montar()
        self.after(100, self._drenar_fila)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)

    def _ao_fechar(self):
        """Salva as chaves digitadas no campo antes de fechar a janela."""
        try:
            chaves, vistas = [], set()
            for l in self.txt_chaves.get("1.0", "end").splitlines():
                k = l.strip()
                if k and k not in vistas:
                    vistas.add(k); chaves.append(k)
            salvar_chaves(chaves)
        except Exception:
            pass
        self.destroy()

    def _montar(self):
        pad = {"padx": 8, "pady": 4}

        topo = ttk.LabelFrame(self, text="1) Palavras-chave  (uma por linha)")
        topo.pack(fill="x", **pad)
        self.txt_kw = tk.Text(topo, height=4, wrap="word")
        self.txt_kw.pack(fill="x", padx=8, pady=8)

        filtros = ttk.LabelFrame(self, text="2) Filtros  (mexa como quiser antes de buscar)")
        filtros.pack(fill="x", **pad)

        self.var_subs = tk.StringVar(value="1000")
        self.var_views = tk.StringVar(value="10000")
        self.var_idade = tk.StringVar(value="60")
        self.var_periodo = tk.StringVar(value="7")
        self.var_paginas = tk.StringVar(value="2")
        self.var_dur_min = tk.StringVar(value="3")
        self.var_dur_max = tk.StringVar(value="0")
        self.var_dur_busca = tk.StringVar(value="Longo (+20 min)")
        self.var_ordenar = tk.StringVar(value="Mais views")
        self.var_idioma = tk.StringVar(value="Todos os idiomas")

        l1 = ttk.Frame(filtros); l1.pack(fill="x", padx=8, pady=6)
        self._campo(l1, "Inscritos minimos:", self.var_subs, 0)
        self._campo(l1, "Views minimas (no periodo):", self.var_views, 2)
        self._campo(l1, "Idade max. do 1o video (dias):", self.var_idade, 4)

        l2 = ttk.Frame(filtros); l2.pack(fill="x", padx=8, pady=6)
        self._campo(l2, "Buscar videos dos ultimos (dias):", self.var_periodo, 0)
        self._campo(l2, "Paginas por palavra-chave (50 cada):", self.var_paginas, 2)
        ttk.Label(l2, text="Idioma da busca:").grid(row=0, column=4, sticky="w")
        ttk.Combobox(l2, textvariable=self.var_idioma, width=15, state="readonly",
                     values=["Todos os idiomas", "Português", "Francês", "Inglês", "Espanhol"]
                     ).grid(row=0, column=5, sticky="w", padx=(4, 16))

        l3 = ttk.Frame(filtros); l3.pack(fill="x", padx=8, pady=6)
        ttk.Label(l3, text="Filtro na busca:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(l3, textvariable=self.var_dur_busca, width=17, state="readonly",
                     values=["Qualquer duracao", "Medio (4-20 min)", "Longo (+20 min)"]
                     ).grid(row=0, column=1, sticky="w", padx=(4, 16))
        self._campo(l3, "Corte fino MIN (min):", self.var_dur_min, 2)
        self._campo(l3, "Corte fino MAX (0=sem):", self.var_dur_max, 4)

        chaves = ttk.LabelFrame(self, text="3) Chaves da API  (uma por linha; ele faz rodizio quando uma esgota)")
        chaves.pack(fill="x", **pad)
        self.txt_chaves = tk.Text(chaves, height=3, wrap="none")
        self.txt_chaves.pack(fill="x", padx=8, pady=8)
        chaves_salvas = carregar_chaves()
        if chaves_salvas:
            self.txt_chaves.insert("1.0", "\n".join(chaves_salvas))

        botoes = ttk.Frame(self); botoes.pack(fill="x", **pad)
        self.btn_buscar = ttk.Button(botoes, text="🔎  PESQUISAR", command=self._iniciar)
        self.btn_buscar.pack(side="left")
        self.btn_parar = ttk.Button(botoes, text="⏹️  Parar", command=self._parar, state="disabled")
        self.btn_parar.pack(side="left", padx=8)
        self.btn_csv = ttk.Button(botoes, text="📂  Abrir planilha", command=self._abrir_csv, state="disabled")
        self.btn_csv.pack(side="left", padx=8)
        self.btn_tags = ttk.Button(botoes, text="🏷️  Extrair Tags", command=self._extrair_tags, state="disabled")
        self.btn_tags.pack(side="left", padx=8)
        ttk.Label(botoes, text="Ordenar por:").pack(side="left", padx=(16, 4))
        cb_ord = ttk.Combobox(botoes, textvariable=self.var_ordenar, width=22, state="readonly",
                              values=["Mais views", "1o video mais recente",
                                      "1o video mais antigo", "Mais inscritos"])
        cb_ord.pack(side="left")
        cb_ord.bind("<<ComboboxSelected>>", self._reordenar)

        status = ttk.Frame(self); status.pack(fill="x", **pad)
        self.lbl_status = ttk.Label(status, text="Pronto."); self.lbl_status.pack(side="left")
        self.btn_novos = ttk.Button(status, text="👁️  Só novidades", command=self._toggle_novos, state="disabled")
        self.btn_novos.pack(side="right")

        meio = ttk.LabelFrame(self, text="Resultados  (clique 2x num canal pra abrir no navegador)  •  ✨ novidade  •  👀 1-2 videos +10k  •  💎 3+ videos +10k  •  💀 3+ e TODOS +10k")
        meio.pack(fill="both", expand=True, **pad)
        cols = ("🔥", "Novidade", "Canal", "Inscritos", "Views", "Duracao", "Video em alta", "1o video", "Palavra-chave")
        self.tree = ttk.Treeview(meio, columns=cols, show="headings", height=10)
        larguras = (40, 90, 200, 80, 80, 70, 240, 90, 110)
        for c, w in zip(cols, larguras):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        self.tree.column("🔥", anchor="center")
        self.tree.column("Novidade", anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(meio, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", self._abrir_canal)
        self._links = {}

        base = ttk.LabelFrame(self, text="O que esta acontecendo")
        base.pack(fill="both", expand=False, **pad)
        self.log = scrolledtext.ScrolledText(base, height=7, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=8, pady=8)

    def _campo(self, parent, rotulo, var, col):
        ttk.Label(parent, text=rotulo).grid(row=0, column=col, sticky="w")
        ttk.Entry(parent, textvariable=var, width=10).grid(row=0, column=col + 1, sticky="w", padx=(4, 16))

    def _logar(self, txt):
        self.log.configure(state="normal")
        self.log.insert("end", txt + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _ler_int(self, var, nome):
        try:
            return int(str(var.get()).strip().replace(".", "").replace(",", ""))
        except Exception:
            raise ValueError("O campo '%s' precisa ser um numero." % nome)

    def _ler_min_seg(self, var, nome):
        txt = str(var.get()).strip().replace(",", ".")
        if txt == "":
            return 0
        try:
            return int(round(float(txt) * 60))
        except Exception:
            raise ValueError("O campo '%s' precisa ser um numero (minutos)." % nome)

    def _iniciar(self):
        try:
            keywords = [l.strip() for l in self.txt_kw.get("1.0", "end").splitlines() if l.strip()]
            if not keywords:
                messagebox.showwarning("Faltou algo", "Digite pelo menos uma palavra-chave.")
                return
            chaves, vistas = [], set()
            for l in self.txt_chaves.get("1.0", "end").splitlines():
                k = l.strip()
                if k and k not in vistas:
                    vistas.add(k); chaves.append(k)
            if not chaves:
                messagebox.showwarning("Faltou a chave", "Cole pelo menos uma chave da API.")
                return
            salvar_chaves(chaves)
            mapa_dur = {"Qualquer duracao": "any", "Medio (4-20 min)": "medium", "Longo (+20 min)": "long"}
            mapa_idioma = {"Todos os idiomas": "", "Português": "pt", "Francês": "fr",
                           "Inglês": "en", "Espanhol": "es"}
            cfg = {
                "keywords": keywords,
                "min_subs": self._ler_int(self.var_subs, "Inscritos minimos"),
                "min_views": self._ler_int(self.var_views, "Views minimas"),
                "max_first_age": self._ler_int(self.var_idade, "Idade max. do 1o video"),
                "search_days": self._ler_int(self.var_periodo, "Buscar videos dos ultimos (dias)"),
                "paginas": max(1, self._ler_int(self.var_paginas, "Paginas por palavra-chave")),
                "min_dur_seg": self._ler_min_seg(self.var_dur_min, "Corte fino MIN"),
                "max_dur_seg": self._ler_min_seg(self.var_dur_max, "Corte fino MAX"),
                "video_duration": mapa_dur.get(self.var_dur_busca.get(), "any"),
                "idioma": mapa_idioma.get(self.var_idioma.get(), ""),
                "ordenar": self.var_ordenar.get(),
                "km": KeyManager(chaves),
            }
            self.km = cfg["km"]   # salva para reusar na extracao de tags
        except ValueError as e:
            messagebox.showerror("Filtro invalido", str(e))
            return

        for i in self.tree.get_children():
            self.tree.delete(i)
        self._links.clear()
        self.resultados = []
        self.log.configure(state="normal"); self.log.delete("1.0", "end"); self.log.configure(state="disabled")

        self.btn_buscar.configure(state="disabled")
        self.btn_parar.configure(state="normal")
        self.btn_csv.configure(state="disabled")
        self.btn_tags.configure(state="disabled")
        self.so_novos = False
        self.btn_novos.configure(text="👁️  Só novidades", state="disabled")
        self.lbl_status.configure(text="Buscando...")
        self._logar("Iniciando: %d palavra(s)-chave, %d chave(s) de API.\n" % (len(keywords), len(chaves)))

        threading.Thread(target=rodar_mineracao, args=(cfg, self.q), daemon=True).start()

    def _drenar_fila(self):
        try:
            while True:
                tipo, dado = self.q.get_nowait()
                if tipo == "log":
                    self._logar(dado)
                elif tipo == "row":
                    self.resultados.append(dado)
                    self._inserir_linha(dado)
                elif tipo == "done":
                    n = len(dado["results"])
                    self.ultimo_csv = dado["csv"]
                    parcial = dado.get("parcial")
                    cancelado = dado.get("cancelado")
                    novos = sum(1 for r in dado["results"] if r.get("Novidade") == "novo")
                    self.btn_buscar.configure(state="normal")
                    self.btn_parar.configure(state="disabled")
                    tocar_som("ok")   # o "plin" de fim de pesquisa
                    if n:
                        self.btn_csv.configure(state="normal")
                        self.btn_tags.configure(state="normal")
                        self.btn_novos.configure(state="normal")
                        if cancelado:
                            self.lbl_status.configure(
                                text="Parado — entreguei %d canal(is) (%d novidade(s))." % (n, novos))
                            self._logar("\n⏹️ Busca interrompida por você.")
                            self._logar("Salvei os %d canais coletados ate aqui (%d novidade(s))." % (n, novos))
                            self._logar("O que aparece '—' (ou 'nao verificado' na planilha) e o que nao deu")
                            self._logar("pra checar porque você parou antes.")
                        elif parcial:
                            self.lbl_status.configure(
                                text="Cota acabou no meio — %d canal(is) (%d novidade(s))." % (n, novos))
                            self._logar("\n⚠️ A cota das chaves acabou no meio da pesquisa.")
                            self._logar("Mesmo assim, salvei os %d canais que consegui coletar (%d novidade(s))." % (n, novos))
                            self._logar("O que aparece '—' (ou 'nao verificado' na planilha) e o que nao deu pra")
                            self._logar("checar por falta de cota. Rode de novo amanha (a cota zera) ou com mais")
                            self._logar("chaves de outros projetos pra completar a verificacao.")
                        else:
                            self.lbl_status.configure(
                                text="Pronto! %d canal(is) — %d novidade(s)." % (n, novos))
                            self._logar("\n✅ FIM. %d canal(is) bateram todos os filtros (%d novidade(s))." % (n, novos))
                        self._logar("Planilha salva em:\n%s" % dado["csv"])
                    else:
                        if cancelado:
                            self.lbl_status.configure(text="Parado antes de coletar canais.")
                            self._logar("\n⏹️ Você parou a busca antes de qualquer canal ser coletado.")
                        elif parcial:
                            self.lbl_status.configure(text="Cota acabou antes de coletar canais.")
                            self._logar("\n⚠️ A cota das chaves acabou cedo demais e nenhum canal foi coletado.")
                            self._logar("Tente de novo amanha (a cota zera) ou adicione chaves de outros projetos.")
                        else:
                            self.lbl_status.configure(text="Terminou: nenhum canal bateu os filtros.")
                            self._logar("\nNenhum canal passou em TODOS os filtros desta vez.")
                            self._logar("Dica: afrouxe um filtro (idade 90, views 5000) ou troque as palavras-chave.")
                elif tipo == "tags":
                    self.btn_tags.configure(state="normal")
                    self.lbl_status.configure(text="Tags extraidas!")
                    self._mostrar_tags(dado)
                elif tipo == "error":
                    self.btn_buscar.configure(state="normal")
                    self.btn_parar.configure(state="disabled")
                    self.lbl_status.configure(text="Deu erro.")
                    self._logar("\n❌ " + dado)
                    tocar_som("erro")
                    messagebox.showerror("Erro", dado)
        except queue.Empty:
            pass
        self.after(120, self._drenar_fila)

    def _parar(self):
        """Pede pra busca parar. Ela encerra com elegancia e entrega o que ja coletou."""
        if self.km:
            self.km.cancelado = True
        self.btn_parar.configure(state="disabled")
        self.lbl_status.configure(text="Parando... vou entregar o que ja tem.")
        self._logar("\n⏹️ Você pediu pra parar. Encerrando e entregando o que ja foi coletado...")

    def _toggle_novos(self):
        """Liga/desliga o filtro que esconde os canais que ja apareceram antes."""
        self.so_novos = not self.so_novos
        self.btn_novos.configure(text=("👁️  Mostrar todos" if self.so_novos else "👁️  Só novidades"))
        self._preencher_tabela()

    def _inserir_linha(self, r):
        nov = "✨ novo" if r.get("Novidade") == "novo" else "visto"
        iid = self.tree.insert("", "end", values=(
            r.get("Icone", ""), nov,
            r["Canal"], _txt(r["Inscritos"]), _txt(r["Views do video"]), r["Duracao"],
            r["Video em alta"], r["1o video"] or "—", r["Palavra-chave"],
        ))
        self._links[iid] = (r["Link do canal"], r["Link do video"])

    def _preencher_tabela(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self._links.clear()
        for r in self.resultados:
            if self.so_novos and r.get("Novidade") != "novo":
                continue   # filtro "so novidades" ligado: pula os ja vistos
            self._inserir_linha(r)

    def _reordenar(self, _=None):
        if not self.resultados:
            return
        self.resultados = ordenar_resultados(self.resultados, self.var_ordenar.get())
        self._preencher_tabela()

    def _abrir_canal(self, _):
        sel = self.tree.selection()
        if sel and sel[0] in self._links:
            webbrowser.open(self._links[sel[0]][0])

    def _abrir_csv(self):
        if self.ultimo_csv and os.path.exists(self.ultimo_csv):
            try:
                os.startfile(self.ultimo_csv)
            except AttributeError:
                webbrowser.open("file://" + self.ultimo_csv)

    def _extrair_tags(self):
        if not self.resultados or not self.km:
            return
        video_ids = []
        for r in self.resultados:
            link = r.get("Link do video", "")
            if "v=" in link:
                video_ids.append(link.split("v=")[1])
        if not video_ids:
            messagebox.showinfo("Sem videos", "Nenhum video encontrado nos resultados.")
            return
        self.btn_tags.configure(state="disabled")
        self.lbl_status.configure(text="Extraindo tags...")
        self._logar("\nExtraindo tags de %d video(s)..." % len(video_ids))

        def _tarefa():
            try:
                tags = extrair_tags_dos_videos(video_ids, self.km)
                self.q.put(("tags", tags))
            except ApiError as e:
                self.q.put(("error", str(e)))
            except Exception as e:
                self.q.put(("error", "Erro ao extrair tags: %s" % e))

        threading.Thread(target=_tarefa, daemon=True).start()

    def _mostrar_tags(self, tags):
        win = tk.Toplevel(self)
        win.title("Tags extraidas  (%d unicas)" % len(tags))
        win.geometry("520x620")
        win.minsize(360, 300)

        ttk.Label(win, text="%d tags unicas encontradas nos videos dos resultados:" % len(tags)
                  ).pack(padx=12, pady=(12, 4), anchor="w")

        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=12, pady=4)
        txt = scrolledtext.ScrolledText(frame, wrap="word")
        txt.pack(fill="both", expand=True)
        conteudo = "\n".join(tags) if tags else "(nenhuma tag encontrada — os videos podem nao ter tags cadastradas)"
        txt.insert("1.0", conteudo)
        txt.configure(state="disabled")

        def copiar():
            win.clipboard_clear()
            win.clipboard_append("\n".join(tags))
            messagebox.showinfo("Copiado!", "%d tags copiadas para a area de transferencia." % len(tags), parent=win)

        rodape = ttk.Frame(win)
        rodape.pack(fill="x", padx=12, pady=8)
        ttk.Button(rodape, text="📋  Copiar tudo", command=copiar).pack(side="left")
        ttk.Button(rodape, text="Fechar", command=win.destroy).pack(side="right")

        self._logar("✅ %d tags unicas extraidas." % len(tags))


if __name__ == "__main__":
    App().mainloop()
