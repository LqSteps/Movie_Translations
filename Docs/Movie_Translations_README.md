# Movie_Translations

Serviço Python automatizado para extração de metadados multilíngues (títulos, sinopses) de **filmes, séries, temporadas e episódios** via TMDB API, organizando os arquivos em subpastas por collections e temporadas.

## Visão Geral

O Módulo de Traduções lê títulos da planilha Google Sheets, busca cada item no TMDB (usando **Collections** para franquias), e extrai **todas as traduções disponíveis** para filmes, séries, temporadas e episódios. O sistema também armazena metadados completos e créditos em inglês.

## Funcionalidades Principais

- **Collections Automáticas**: Detecta franquias como James Bond, Harry Potter, etc.
- **Busca Hierárquica**: Extrai traduções para Série → Temporada → Episódio
- **Multi-formato**: Salva dados em `.json` e `.csv`
- **Estrutura Organizada**: Cria subpastas para collections, séries e temporadas
- **Popularidade Mínima**: Filtra resultados com popularidade >= 5.0

### Formatos de Input Suportados

| Formato | Descrição | Exemplo | Resultado |
|---------|-----------|---------|-----------|
| `Nome` | Busca collection primeiro, senão todas as versões | `James Bond` | Toda a collection (25+ filmes) |
| `Nome - YYYY` | Filme específico do ano | `Batman - 2022` | Apenas The Batman (2022) |
| `Nome - s1` | Série, temporada 1 (com episódios) | `Severance - s1` | Temporada 1 + todos os episódios |
| `Nome - s` | Série, todas as temporadas (com episódios) | `Breaking Bad - s` | Todas temporadas + episódios |

### Estrutura de Pastas Organizada

```
Traduções/
├── James Bond Collection/
│   ├── Casino_Royale_2006_info.json
│   ├── Casino_Royale_2006_translations.json
│   ├── Casino_Royale_2006_translations.csv
│   ├── Skyfall_2012_info.json
│   └── ...
└── [SERIE] Severance/
    ├── Season 1/
    │   ├── Season_info.json
    │   ├── Season_translations.json
    │   ├── Season_translations.csv
    │   └── Episodes/
    │       ├── E01_info.json
    │       ├── E01_translations.json
    │       ├── E01_translations.csv
    │       ├── E02_info.json
    │       └── ...
    └── Season 2/
        ├── Season_info.json
        └── Episodes/
            └── ...
```

## Formato dos Arquivos de Saída

### `_translations.json`

```json
[
  {
    "titulo_original": "Severance",
    "tmdb_id": 95396,
    "tipo": "tv_episode",
    "season": 1,
    "episode": 1,
    "idioma": "pt",
    "pais": "BR",
    "nome_idioma": "Portuguese",
    "titulo_traduzido": "Boas Novas Sobre o Inferno",
    "sinopse_traduzida": "Mark S. leva uma nova funcionária..."
  }
]
```

### `_info.json`

Contém metadados completos em inglês (gêneros, elenco, diretores, etc.).

**Exemplo de Filme:**
```json
{
  "id": 370172,
  "type": "movie",
  "title": "No Time to Die",
  "genres": ["Action", "Adventure", "Thriller"],
  "cast": [{"id": 8784, "name": "Daniel Craig"}],
  "directors": [{"id": 39189, "name": "Cary Joji Fukunaga"}],
  "_note": "All data in English"
}
```

**Exemplo de Episódio:**
```json
{
  "id": 1999279,
  "type": "tv_episode",
  "season_number": 1,
  "episode_number": 1,
  "name": "Good News About Hell",
  "overview": "Mark Scout leads a new hire...",
  "air_date": "2022-02-18",
  "runtime": 57,
  "_note": "All data in English"
}
```

## Endpoints TMDB Utilizados

1. **`/search/collection`** - Busca de collections (franquias)
2. **`/collection/{id}`** - Filmes de uma collection
3. **`/search/multi`** - Busca combinada de filmes e séries
4. **`/tv/{id}`** e **`/tv/{id}/season/{num}`** - Detalhes de série e temporada
5. **`/tv/{id}/season/{num}/episode/{ep_num}`** - Detalhes de episódio
6. **`/translations`** - Traduções para cada tipo (filme, série, temporada, episódio)
7. **`/credits`** - Elenco e diretores (apenas para filmes e séries)

## Instalação do Serviço Systemd

Para configurar o serviço para rodar automaticamente:

```bash
# 1. Criar link simbólico do arquivo de serviço
sudo ln -s /caminho/para/repositorio/Services/movie-translations.service /etc/systemd/system/

# 2. Recarregar daemon do systemd
sudo systemctl daemon-reload

# 3. Habilitar serviço para iniciar no boot
sudo systemctl enable movie-translations.service

# 4. Iniciar serviço
sudo systemctl start movie-translations.service

# 5. Verificar status
sudo systemctl status movie-translations.service
```

## Execução Manual

```bash
# Ativar venv
source venv/bin/activate

# Executar
python3 main.py
```
