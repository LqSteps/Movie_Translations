#!/usr/bin/env python3

import os
import pandas as pd
import requests
import json
import time
import csv
import re

# ==============================
# CONFIGURAÇÕES GERAIS
# ==============================

SHEET_URL = "https://docs.google.com/spreadsheets/d/1Mj8CovNSu03bpWnIGp_JntDUhxw5KjLRhbfqr8VfsHk/export?format=csv"
TMDB_API_KEY = "20c117664b56c63145516208a9dd5f5f"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Diretório de saída
OUTPUT_DIR = "/GitHub/Repos/Movie_Translations/Traduções"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================
# FUNÇÕES AUXILIARES
# ==============================

def parse_titulo_ano(texto):
    """Extrai título e ano"""
    match = re.match(r'^(.+?)\s*\((\d{4})\)\s*$', texto)
    if match:
        return match.group(1).strip(), match.group(2)

    match = re.match(r'^(.+?)\s*-\s*(\d{4})\s*$', texto)
    if match:
        return match.group(1).strip(), match.group(2)

    return texto.strip(), None

# ==============================
# FUNÇÕES PRINCIPAIS
# ==============================

def ler_filmes_url(url):
    """Lê filmes direto da URL pública do Google Sheets"""
    df = pd.read_csv(url)
    return df

def buscar_filme(titulo, ano=None):
    """Busca FILME no TMDb"""
    url = f"{TMDB_BASE_URL}/search/movie"
    # MUDANÇA: language="en-US" para buscar em inglês
    params = {"api_key": TMDB_API_KEY, "query": titulo, "language": "en-US"}

    if ano:
        params["primary_release_year"] = ano

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])

        if results:
            result = results[0]
            release_year = result.get("release_date", "")[:4]

            if ano and release_year != ano:
                return None

            return {
                "id": result["id"],
                "type": "movie",
                "title": result["title"],
                "original_title": result.get("original_title", ""),
                "release_date": result.get("release_date", ""),
                "year": release_year
            }
        return None
    except Exception as e:
        print(f"    Erro ao buscar filme: {e}")
        return None

def buscar_serie(titulo, ano=None):
    """Busca SÉRIE no TMDb"""
    url = f"{TMDB_BASE_URL}/search/tv"
    # MUDANÇA: language="en-US" para buscar em inglês
    params = {"api_key": TMDB_API_KEY, "query": titulo, "language": "en-US"}

    if ano:
        params["first_air_date_year"] = ano

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])

        if results:
            result = results[0]
            first_air_year = result.get("first_air_date", "")[:4]

            if ano and first_air_year != ano:
                return None

            return {
                "id": result["id"],
                "type": "tv",
                "title": result["name"],
                "original_title": result.get("original_name", ""),
                "release_date": result.get("first_air_date", ""),
                "year": first_air_year
            }
        return None
    except Exception as e:
        print(f"    Erro ao buscar série: {e}")
        return None

def buscar_conteudo(titulo, ano=None):
    """Busca FILME ou SÉRIE automaticamente"""
    print(f"  🎬 Buscando como filme...")
    content = buscar_filme(titulo, ano)
    if content:
        print(f"  ✓ Filme encontrado: {content['title']} ({content['year']})")
        return content

    print(f"  📺 Buscando como série...")
    content = buscar_serie(titulo, ano)
    if content:
        print(f"  ✓ Série encontrada: {content['title']} ({content['year']})")
        return content

    if ano:
        print(f"  ⚠ Não encontrado com ano {ano}")
        return None

    print(f"  ✗ Não encontrado")
    return None

def obter_traducoes(content_id, content_type):
    """Obtém todas as traduções"""
    url = f"{TMDB_BASE_URL}/{content_type}/{content_id}/translations"
    params = {"api_key": TMDB_API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("translations", [])
    except Exception as e:
        print(f"  ⚠ Erro ao obter traduções: {e}")
        return []

def obter_detalhes(content_id, content_type):
    """Obtém detalhes completos EM INGLÊS"""
    url = f"{TMDB_BASE_URL}/{content_type}/{content_id}"
    # MUDANÇA: language="en-US" para detalhes em inglês
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return {
            "id": data.get("id"),
            "type": content_type,
            "title": data.get("title" if content_type == "movie" else "name"),
            "original_title": data.get("original_title" if content_type == "movie" else "original_name"),
            "release_date": data.get("release_date" if content_type == "movie" else "first_air_date", ""),
            "overview": data.get("overview", ""),  # Sinopse em inglês
            "vote_average": data.get("vote_average", 0),
            "vote_count": data.get("vote_count", 0),
            "popularity": data.get("popularity", 0),
            "original_language": data.get("original_language", ""),
            "adult": data.get("adult", False),
            "genres": [g["name"] for g in data.get("genres", [])],  # Gêneros em inglês
            "runtime": data.get("runtime") if content_type == "movie" else None,
            "number_of_seasons": data.get("number_of_seasons") if content_type == "tv" else None,
            "number_of_episodes": data.get("number_of_episodes") if content_type == "tv" else None,
            "status": data.get("status", "")  # Status em inglês
        }
    except Exception as e:
        print(f"  ⚠ Erro ao obter detalhes: {e}")
        return {}

def obter_creditos(content_id, content_type):
    """Obtém elenco e diretores EM INGLÊS"""
    url = f"{TMDB_BASE_URL}/{content_type}/{content_id}/credits"
    # MUDANÇA: language="en-US" para nomes em inglês
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Elenco principal (top 10)
        cast = data.get("cast", [])
        elenco_principal = []
        for person in cast[:10]:
            elenco_principal.append({
                "id": person.get("id"),
                "name": person.get("name"),
                "character": person.get("character"),
                "order": person.get("order", 999)
            })

        # Diretores
        crew = data.get("crew", [])
        diretores = []
        for person in crew:
            if person.get("job") == "Director":
                diretores.append({
                    "id": person.get("id"),
                    "name": person.get("name"),
                    "job": person.get("job")
                })

        return {
            "cast": elenco_principal,
            "directors": diretores
        }
    except Exception as e:
        print(f"  ⚠ Erro ao obter créditos: {e}")
        return {"cast": [], "directors": []}

def salvar_traducao_filme(nome_filme, traducoes, detalhes, creditos, ano_planilha=None):
    """Salva as traduções e informações"""
    nome_base = nome_filme.replace(" ", "_").replace("/", "_")

    if ano_planilha:
        nome_base = f"{nome_base}_{ano_planilha}"

    if detalhes.get("type") == "tv":
        nome_base = f"[SERIE]_{nome_base}"

    translations_json_path = os.path.join(OUTPUT_DIR, f"{nome_base}_translations.json")
    translations_csv_path = os.path.join(OUTPUT_DIR, f"{nome_base}_translations.csv")
    info_json_path = os.path.join(OUTPUT_DIR, f"{nome_base}_info.json")

    # Salvar traduções
    with open(translations_json_path, "w", encoding="utf-8") as json_file:
        json.dump(traducoes, json_file, ensure_ascii=False, indent=4)

    if traducoes:
        with open(translations_csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=traducoes[0].keys())
            writer.writeheader()
            writer.writerows(traducoes)

    # Salvar info (EM INGLÊS)
    info_completa = {
        **detalhes,
        **creditos,
        "_note": "All data in English. Use translations.json for localized content."
    }

    with open(info_json_path, "w", encoding="utf-8") as json_file:
        json.dump(info_completa, json_file, ensure_ascii=False, indent=4)

    print(f"  💾 Traduções: {translations_json_path}")
    print(f"  💾 Info (EN): {info_json_path}")

def processar_filmes(sheet_url):
    """Processa os filmes/séries"""
    print("📥 Baixando planilha...")
    df_filmes = ler_filmes_url(sheet_url)

    print(f"Colunas: {df_filmes.columns.tolist()}")
    print(f"Total de linhas: {len(df_filmes)}\n")

    coluna = df_filmes.columns[0]

    total_traducoes = 0
    filmes_processados = 0
    series_processadas = 0
    pulados = 0

    for idx, titulo_raw in enumerate(df_filmes[coluna], 1):
        if pd.isna(titulo_raw) or str(titulo_raw).strip() == "":
            continue

        titulo_raw = str(titulo_raw).strip()
        titulo, ano = parse_titulo_ano(titulo_raw)

        if ano:
            print(f"[{idx}/{len(df_filmes)}] 🎬 {titulo} ({ano})")
        else:
            print(f"[{idx}/{len(df_filmes)}] 🎬 {titulo}")

        content = buscar_conteudo(titulo, ano)

        if content:
            content_id = content["id"]
            content_type = content["type"]

            traducoes = obter_traducoes(content_id, content_type)
            print(f"  ✓ {len(traducoes)} traduções encontradas")

            print(f"  📊 Obtendo detalhes em inglês...")
            detalhes = obter_detalhes(content_id, content_type)

            print(f"  👥 Obtendo créditos em inglês...")
            creditos = obter_creditos(content_id, content_type)
            print(f"     {len(creditos['cast'])} atores | {len(creditos['directors'])} diretores")

            dados_filme = []
            for trad in traducoes:
                dados_filme.append({
                    "titulo_original": content["original_title"],
                    "tmdb_id": content_id,
                    "tipo": content_type,
                    "idioma": trad.get("iso_639_1", ""),
                    "pais": trad.get("iso_3166_1", ""),
                    "nome_idioma": trad.get("english_name", ""),
                    "titulo_traduzido": trad["data"].get("title" if content_type == "movie" else "name", ""),
                    "sinopse_traduzida": trad["data"].get("overview", "")
                })

            salvar_traducao_filme(
                content["title"],
                dados_filme,
                detalhes,
                creditos,
                ano_planilha=ano
            )

            total_traducoes += len(traducoes)

            if content_type == "movie":
                filmes_processados += 1
            else:
                series_processadas += 1
        else:
            print(f"  ✗ Não encontrado")
            pulados += 1

        time.sleep(0.3)
        print()

    print("=" * 60)
    print(f"✓ {total_traducoes} traduções exportadas")
    print(f"✓ {filmes_processados} filmes processados")
    print(f"✓ {series_processadas} séries processadas")
    print(f"⚠ {pulados} itens pulados")
    print("=" * 60)
    print()

# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================

if __name__ == "__main__":
    try:
        processar_filmes(SHEET_URL)
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
