#!/usr/bin/env python3
"""
TMDB Traduções - Collections + Subpastas + Episódios
"""

import os
import pandas as pd
import requests
import json
import time
import csv
import re
from difflib import SequenceMatcher

SHEET_URL = "https://docs.google.com/spreadsheets/d/1Mj8CovNSu03bpWnIGp_JntDUhxw5KjLRhbfqr8VfsHk/export?format=csv"
TMDB_API_KEY = "20c117664b56c63145516208a9dd5f5f"
TMDB_BASE_URL = "https://api.themoviedb.org/3"
OUTPUT_DIR = "/GitHub/Repos/Movie_Translations/Traduções"

MIN_POPULARITY = 5.0
MIN_TITLE_SIMILARITY = 0.6

os.makedirs(OUTPUT_DIR, exist_ok=True)

def title_similarity(a, b):
    """Similaridade de título"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def parse_input(text):
    """Parse"""
    match = re.match(r'^(.+?)\s*-\s*s(\d+)?\s*$', text, re.IGNORECASE)
    if match:
        title = match.group(1).strip()
        season_str = match.group(2)
        season = int(season_str) if season_str else "all"
        return title, None, season
    
    match = re.match(r'^(.+?)\s*-\s*(\d{4})\s*$', text)
    if match:
        return match.group(1).strip(), match.group(2), None
    
    return text.strip(), None, None

def ler_filmes_url(url):
    """Lê planilha"""
    df = pd.read_csv(url)
    return df

def search_collection(title):
    """Busca collection"""
    try:
        url = f"{TMDB_BASE_URL}/search/collection"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "language": "en-US"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            return None, None
        
        results = sorted(data["results"], key=lambda x: x.get("popularity", 0), reverse=True)
        collection = results[0]
        return collection.get("id"), collection.get("name")
        
    except Exception as e:
        return None, None

def get_collection_movies(collection_id):
    """Pega filmes da collection"""
    try:
        url = f"{TMDB_BASE_URL}/collection/{collection_id}"
        params = {"api_key": TMDB_API_KEY, "language": "en-US"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        parts = data.get("parts", [])
        
        if not parts:
            return None, None
        
        parts = sorted(parts, key=lambda x: x.get("release_date", ""))
        
        collection_name = data.get("name")
        print(f"   📚 Collection: {collection_name} ({len(parts)} filmes)")
        
        converted = []
        for movie in parts:
            year = movie.get("release_date", "")[:4]
            
            converted.append({
                "id": movie["id"],
                "type": "movie",
                "title": movie["title"],
                "original_title": movie.get("original_title", ""),
                "release_date": movie.get("release_date", ""),
                "year": year,
                "popularity": movie.get("popularity", 0),
                "collection_name": collection_name
            })
        
        return converted, collection_name
        
    except Exception as e:
        return None, None

def search_multi(title, year=None, get_all=False):
    """Busca multi"""
    try:
        url = f"{TMDB_BASE_URL}/search/multi"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "language": "en-US"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            return None
        
        results = [r for r in data["results"] if r.get("media_type") in ["movie", "tv"]]
        
        if not results:
            return None
        
        results = [r for r in results if r.get("popularity", 0) >= MIN_POPULARITY]
        
        if not results:
            return None
        
        for r in results:
            result_title = r.get("title") if r["media_type"] == "movie" else r.get("name", "")
            original_title = r.get("original_title") if r["media_type"] == "movie" else r.get("original_name", "")
            
            sim1 = title_similarity(title, result_title)
            sim2 = title_similarity(title, original_title)
            r["title_similarity"] = max(sim1, sim2)
        
        if not get_all:
            results = [r for r in results if r.get("title_similarity", 0) >= MIN_TITLE_SIMILARITY]
            
            if not results:
                return None
        
        if year:
            year_filtered = []
            for r in results:
                if r["media_type"] == "movie":
                    r_year = r.get("release_date", "")[:4]
                else:
                    r_year = r.get("first_air_date", "")[:4]
                
                if r_year == year:
                    year_filtered.append(r)
            
            if year_filtered:
                results = year_filtered
            else:
                return None
        
        results = sorted(results, key=lambda x: x.get("popularity", 0), reverse=True)
        
        if not get_all:
            results = [results[0]]
        
        converted_results = []
        for result in results:
            media_type = result["media_type"]
            
            if media_type == "movie":
                release_year = result.get("release_date", "")[:4]
                
                converted_results.append({
                    "id": result["id"],
                    "type": "movie",
                    "title": result["title"],
                    "original_title": result.get("original_title", ""),
                    "release_date": result.get("release_date", ""),
                    "year": release_year,
                    "popularity": result.get("popularity", 0)
                })
            
            else:
                first_air_year = result.get("first_air_date", "")[:4]
                
                converted_results.append({
                    "id": result["id"],
                    "type": "tv",
                    "title": result["name"],
                    "original_title": result.get("original_name", ""),
                    "release_date": result.get("first_air_date", ""),
                    "year": first_air_year,
                    "popularity": result.get("popularity", 0)
                })
        
        return converted_results if get_all else converted_results[0]
        
    except Exception as e:
        return None

def get_tv_seasons(tv_id):
    """Lista temporadas"""
    try:
        url = f"{TMDB_BASE_URL}/tv/{tv_id}"
        params = {"api_key": TMDB_API_KEY, "language": "en-US"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        seasons = data.get("seasons", [])
        seasons = [s for s in seasons if s.get("season_number", 0) > 0]
        
        return [s["season_number"] for s in seasons]
    except Exception as e:
        return []

def get_season_episodes(tv_id, season_number):
    """Lista episódios de uma temporada"""
    try:
        url = f"{TMDB_BASE_URL}/tv/{tv_id}/season/{season_number}"
        params = {"api_key": TMDB_API_KEY, "language": "en-US"}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        episodes = data.get("episodes", [])
        
        return [ep.get("episode_number") for ep in episodes]
    except Exception as e:
        return []

def obter_traducoes(content_id, content_type, season=None, episode=None):
    """Obtém traduções"""
    if content_type == "tv" and season is not None and episode is not None:
        url = f"{TMDB_BASE_URL}/tv/{content_id}/season/{season}/episode/{episode}/translations"
    elif content_type == "tv" and season is not None:
        url = f"{TMDB_BASE_URL}/tv/{content_id}/season/{season}/translations"
    else:
        url = f"{TMDB_BASE_URL}/{content_type}/{content_id}/translations"
    
    params = {"api_key": TMDB_API_KEY}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("translations", [])
    except Exception as e:
        return []

def obter_detalhes(content_id, content_type, season=None, episode=None):
    """Obtém detalhes"""
    if content_type == "tv" and season is not None and episode is not None:
        url = f"{TMDB_BASE_URL}/tv/{content_id}/season/{season}/episode/{episode}"
    elif content_type == "tv" and season is not None:
        url = f"{TMDB_BASE_URL}/tv/{content_id}/season/{season}"
    else:
        url = f"{TMDB_BASE_URL}/{content_type}/{content_id}"
    
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if content_type == "tv" and season is not None and episode is not None:
            return {
                "id": data.get("id"),
                "type": "tv_episode",
                "season_number": season,
                "episode_number": episode,
                "name": data.get("name"),
                "overview": data.get("overview", ""),
                "air_date": data.get("air_date", ""),
                "runtime": data.get("runtime"),
                "vote_average": data.get("vote_average", 0)
            }
        
        if content_type == "tv" and season is not None:
            return {
                "id": data.get("id"),
                "type": "tv_season",
                "season_number": season,
                "name": data.get("name"),
                "overview": data.get("overview", ""),
                "air_date": data.get("air_date", ""),
                "episode_count": data.get("episode_count", 0)
            }
        
        return {
            "id": data.get("id"),
            "type": content_type,
            "title": data.get("title" if content_type == "movie" else "name"),
            "original_title": data.get("original_title" if content_type == "movie" else "original_name"),
            "release_date": data.get("release_date" if content_type == "movie" else "first_air_date", ""),
            "overview": data.get("overview", ""),
            "vote_average": data.get("vote_average", 0),
            "popularity": data.get("popularity", 0),
            "genres": [g["name"] for g in data.get("genres", [])],
            "runtime": data.get("runtime") if content_type == "movie" else None,
            "number_of_seasons": data.get("number_of_seasons") if content_type == "tv" else None,
            "status": data.get("status", "")
        }
    except Exception as e:
        return {}

def obter_creditos(content_id, content_type):
    """Obtém créditos"""
    url = f"{TMDB_BASE_URL}/{content_type}/{content_id}/credits"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        cast = data.get("cast", [])
        elenco_principal = []
        for person in cast[:10]:
            elenco_principal.append({
                "id": person.get("id"),
                "name": person.get("name"),
                "character": person.get("character")
            })
        
        crew = data.get("crew", [])
        diretores = []
        for person in crew:
            if person.get("job") == "Director":
                diretores.append({
                    "id": person.get("id"),
                    "name": person.get("name")
                })
        
        return {
            "cast": elenco_principal,
            "directors": diretores
        }
    except Exception as e:
        return {"cast": [], "directors": []}

def get_output_dir(content, season=None, episode=None, collection_name=None):
    """Gera caminho da pasta"""
    safe_title = "".join(c for c in content["title"] if c.isalnum() or c in (' ', '-', '_')).strip()
    year = content["year"]
    content_type = content["type"]
    
    # Filme de collection
    if collection_name and content_type == "movie":
        safe_collection = "".join(c for c in collection_name if c.isalnum() or c in (' ', '-', '_')).strip()
        base_dir = os.path.join(OUTPUT_DIR, safe_collection)
        return base_dir
    
    # Série
    elif content_type == "tv":
        series_dir = os.path.join(OUTPUT_DIR, f"[SERIE] {safe_title}")
        
        if season:
            season_dir = os.path.join(series_dir, f"Season {season}")
            
            if episode:
                episodes_dir = os.path.join(season_dir, "Episodes")
                return episodes_dir
            
            return season_dir
        
        return series_dir
    
    # Filme individual
    else:
        return OUTPUT_DIR

def verificar_arquivo_existe(content, season=None, episode=None, collection_name=None):
    """Verifica se arquivo existe"""
    output_dir = get_output_dir(content, season, episode, collection_name)
    
    safe_title = "".join(c for c in content["title"] if c.isalnum() or c in (' ', '-', '_')).strip()
    year = content["year"]
    
    if episode:
        nome_base = f"E{episode:02d}_info.json"
    elif season:
        nome_base = "Season_info.json"
    else:
        nome_base = f"{safe_title}_{year}_info.json"
    
    info_json_path = os.path.join(output_dir, nome_base)
    
    return os.path.exists(info_json_path)

def salvar_traducao(content, traducoes, detalhes, creditos, season=None, episode=None, collection_name=None):
    """Salva traduções"""
    output_dir = get_output_dir(content, season, episode, collection_name)
    os.makedirs(output_dir, exist_ok=True)
    
    safe_title = "".join(c for c in content["title"] if c.isalnum() or c in (' ', '-', '_')).strip()
    year = content["year"]
    
    if episode:
        nome_base = f"E{episode:02d}"
    elif season:
        nome_base = "Season"
    else:
        nome_base = f"{safe_title}_{year}"
    
    translations_json_path = os.path.join(output_dir, f"{nome_base}_translations.json")
    translations_csv_path = os.path.join(output_dir, f"{nome_base}_translations.csv")
    info_json_path = os.path.join(output_dir, f"{nome_base}_info.json")
    
    with open(translations_json_path, "w", encoding="utf-8") as json_file:
        json.dump(traducoes, json_file, ensure_ascii=False, indent=4)
    
    if traducoes:
        with open(translations_csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=traducoes[0].keys())
            writer.writeheader()
            writer.writerows(traducoes)
    
    info_completa = {
        **detalhes,
        **creditos,
        "_note": "All data in English"
    }
    
    with open(info_json_path, "w", encoding="utf-8") as json_file:
        json.dump(info_completa, json_file, ensure_ascii=False, indent=4)
    
    print(f"         💾 {nome_base}")

def processar_episode(content, season_num, episode_num):
    """Processa episódio individual"""
    if verificar_arquivo_existe(content, season_num, episode_num):
        return "skipped"
    
    traducoes = obter_traducoes(content["id"], "tv", season_num, episode_num)
    
    if not traducoes:
        return None
    
    detalhes = obter_detalhes(content["id"], "tv", season_num, episode_num)
    creditos = {"cast": [], "directors": []}
    
    dados = []
    for trad in traducoes:
        dados.append({
            "titulo_original": content["original_title"],
            "tmdb_id": content["id"],
            "tipo": "tv_episode",
            "season": season_num,
            "episode": episode_num,
            "idioma": trad.get("iso_639_1", ""),
            "pais": trad.get("iso_3166_1", ""),
            "nome_idioma": trad.get("english_name", ""),
            "titulo_traduzido": trad["data"].get("name", ""),
            "sinopse_traduzida": trad["data"].get("overview", "")
        })
    
    salvar_traducao(content, dados, detalhes, creditos, season_num, episode_num)
    return "processed"

def processar_season(content, season_num):
    """Processa temporada + episódios"""
    print(f"      📺 Season {season_num}...")
    
    # Salvar info da temporada
    if not verificar_arquivo_existe(content, season_num):
        traducoes = obter_traducoes(content["id"], "tv", season_num)
        print(f"         ✓ {len(traducoes)} traduções da temporada")
        
        detalhes = obter_detalhes(content["id"], "tv", season_num)
        creditos = {"cast": [], "directors": []}
        
        dados = []
        for trad in traducoes:
            dados.append({
                "titulo_original": content["original_title"],
                "tmdb_id": content["id"],
                "tipo": "tv_season",
                "season": season_num,
                "idioma": trad.get("iso_639_1", ""),
                "pais": trad.get("iso_3166_1", ""),
                "nome_idioma": trad.get("english_name", ""),
                "titulo_traduzido": trad["data"].get("name", ""),
                "sinopse_traduzida": trad["data"].get("overview", "")
            })
        
        salvar_traducao(content, dados, detalhes, creditos, season_num)
    
    # Processar episódios
    episodes = get_season_episodes(content["id"], season_num)
    print(f"         📺 {len(episodes)} episódios")
    
    processed_eps = 0
    skipped_eps = 0
    
    for ep_num in episodes:
        result = processar_episode(content, season_num, ep_num)
        if result == "processed":
            processed_eps += 1
        elif result == "skipped":
            skipped_eps += 1
    
    print(f"         ✓ {processed_eps} episódios processados | {skipped_eps} já existiam")
    
    return "processed"

def processar_filmes(sheet_url):
    """Processa filmes/séries"""
    print("📥 Baixando planilha...\n")
    df_filmes = ler_filmes_url(sheet_url)
    
    coluna = df_filmes.columns[0]
    
    total_items = 0
    pulados = 0
    ja_existem = 0
    
    for idx, titulo_raw in enumerate(df_filmes[coluna], 1):
        if pd.isna(titulo_raw) or str(titulo_raw).strip() == "":
            continue
        
        titulo_raw = str(titulo_raw).strip()
        titulo, ano, season = parse_input(titulo_raw)
        
        print(f"[{idx}/{len(df_filmes)}] 🎬 {titulo_raw}")
        
        # Tentar collection
        contents = None
        collection_name = None
        
        if ano is None and season is None:
            print(f"   🔍 Procurando collection...")
            collection_id, coll_name = search_collection(titulo)
            
            if collection_id:
                contents, collection_name = get_collection_movies(collection_id)
        
        if not contents:
            get_all = (ano is None and season is None)
            contents = search_multi(titulo, ano, get_all=get_all)
        
        if not contents:
            print(f"  ✗ Não encontrado\n")
            pulados += 1
            continue
        
        if not isinstance(contents, list):
            contents = [contents]
        
        print(f"  ✓ {len(contents)} resultado(s)")
        
        for content in contents:
            content_id = content["id"]
            content_type = content["type"]
            
            coll = content.get("collection_name", collection_name)
            
            print(f"\n   {'🎬' if content_type == 'movie' else '📺'} {content['title']} ({content['year']})")
            
            if content_type == "movie" and season is not None:
                print(f"      ⚠️ É filme, ignorando temporada")
                season_to_use = None
            else:
                season_to_use = season
            
            # Série com temporadas
            if content_type == "tv" and season_to_use is not None:
                if season_to_use == "all":
                    seasons = get_tv_seasons(content_id)
                    print(f"      📺 {len(seasons)} temporadas")
                    
                    for s in seasons:
                        processar_season(content, s)
                        time.sleep(0.3)
                    
                    total_items += 1
                    continue
                else:
                    processar_season(content, season_to_use)
                    total_items += 1
                    continue
            
            # Filme ou série sem temporada
            if verificar_arquivo_existe(content, None, None, coll):
                print(f"      ⏭️ Já existe!")
                ja_existem += 1
                continue
            
            traducoes = obter_traducoes(content_id, content_type)
            print(f"      ✓ {len(traducoes)} traduções")
            
            detalhes = obter_detalhes(content_id, content_type)
            creditos = obter_creditos(content_id, content_type)
            
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
            
            salvar_traducao(content, dados_filme, detalhes, creditos, None, None, coll)
            
            total_items += 1
            
            time.sleep(0.3)
        
        print()
    
    print("=" * 60)
    print(f"✓ {total_items} itens processados")
    print(f"⏭️  {ja_existem} já existiam")
    print(f"⚠ {pulados} pulados")
    print("=" * 60)

if __name__ == "__main__":
    try:
        processar_filmes(SHEET_URL)
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
