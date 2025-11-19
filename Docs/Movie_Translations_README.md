# Módulo de Traduções

Serviço Python automatizado para extração de metadados multilíngues (títulos traduzidos e sinopses) de filmes e séries via TMDB API e Google Sheets.

## Visão Geral

O Módulo de Traduções lê títulos de filmes/séries de uma planilha Google Sheets, busca cada item no TMDB e extrai **todas as traduções disponíveis** (títulos e sinopses), além de metadados completos e créditos **em inglês**. O sistema diferencia automaticamente entre filmes e séries.

## Fonte de Dados

### Planilha Google Sheets

**URL da Planilha**: [https://docs.google.com/spreadsheets/d/1Mj8CovNSu03bpWnIGp_JntDUhxw5KjLRhbfqr8VfsHk/export?format=csv](https://docs.google.com/spreadsheets/d/1Mj8CovNSu03bpWnIGp_JntDUhxw5KjLRhbfqr8VfsHk/export?format=csv)

**Formato Suportado**: 

- Coluna única com títulos de filmes/séries
- Formatos aceitos:
  - `Nome do Filme (2024)`
  - `Nome do Filme - 2024`
  - `Nome do Filme` (sem ano)

## Funcionalidades Principais

### Busca Inteligente

- **Detecção automática** de tipo (filme vs. série)
- **Extração de ano** via regex de padrões `(YYYY)` ou `- YYYY`
- **Busca com ano** para maior precisão
- **Fallback sem ano** se não encontrar com ano especificado
- **Validação de ano** entre resultado e planilha

### Metadados Extraídos

#### Traduções (Multilíngues)

- Título traduzido em cada idioma disponível
- Sinopse traduzida em cada idioma disponível
- Código ISO do idioma (`iso_639_1`)
- Código ISO do país (`iso_3166_1`)
- Nome do idioma em inglês

#### Informações Principais (Inglês)

- **Detalhes básicos**: título original, data lançamento, sinopse
- **Métricas**: nota média, contagem de votos, popularidade
- **Classificação**: idioma original, adulto (sim/não), status
- **Gêneros**: lista de gêneros em inglês
- **Filmes**: duração (runtime)
- **Séries**: número de temporadas e episódios

#### Créditos (Inglês)

- **Elenco principal**: Top 10 atores com personagem e ordem
- **Diretores**: Todos os diretores creditados
- **IDs TMDB**: Para todos os membros do elenco/crew

## Estrutura do Projeto

```
Movie_Translations/
├── venv/                           # Ambiente virtual (já configurado)
├── main.py                         # Script principal
├── Traduções/                      # Diretório de saída
│   ├── {filme}_{ano}_translations.json
│   ├── {filme}_{ano}_translations.csv
│   ├── {filme}_{ano}_info.json
│   ├── [SERIE]_{serie}_{ano}_translations.json
│   ├── [SERIE]_{serie}_{ano}_translations.csv
│   └── [SERIE]_{serie}_{ano}_info.json
└── movie-translations.service      # Arquivo systemd
```

## Formato dos Arquivos de Saída

### 1. `{nome}_translations.json`

```json
[
  {
    "titulo_original": "The Matrix",
    "tmdb_id": 603,
    "tipo": "movie",
    "idioma": "pt",
    "pais": "BR",
    "nome_idioma": "Portuguese",
    "titulo_traduzido": "Matrix",
    "sinopse_traduzida": "Um hacker descobre a verdade..."
  },
  {
    "idioma": "es",
    "pais": "ES",
    "nome_idioma": "Spanish",
    "titulo_traduzido": "Matrix",
    "sinopse_traduzida": "Un hacker descubre la verdad..."
  }
]
```

### 2. `{nome}_translations.csv`

Mesmos dados em formato CSV para fácil importação em planilhas.

### 3. `{nome}_info.json`

```json
{
  "id": 603,
  "type": "movie",
  "title": "The Matrix",
  "original_title": "The Matrix",
  "release_date": "1999-03-30",
  "overview": "A computer hacker learns...",
  "vote_average": 8.2,
  "vote_count": 23456,
  "popularity": 58.934,
  "original_language": "en",
  "adult": false,
  "genres": ["Action", "Science Fiction"],
  "runtime": 136,
  "status": "Released",
  "cast": [
    {
      "id": 6384,
      "name": "Keanu Reeves",
      "character": "Neo",
      "order": 0
    }
  ],
  "directors": [
    {
      "id": 899,
      "name": "Lana Wachowski",
      "job": "Director"
    }
  ],
  "_note": "All data in English. Use translations.json for localized content."
}
```

## Endpoints TMDB Utilizados

1. **`/search/movie`** - Busca de filmes (language=en-US)
2. **`/search/tv`** - Busca de séries (language=en-US)
3. **`/{type}/{id}/translations`** - Todas as traduções
4. **`/{type}/{id}`** - Detalhes completos (language=en-US)
5. **`/{type}/{id}/credits`** - Elenco e crew (language=en-US)

## Instalação e Configuração

### Ambiente Virtual (Já Incluído)

O repositório já possui um ambiente virtual (`venv/`) com todas as dependências instaladas. Para ativar:

```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Dependências

```
pandas
requests
```

### Configuração da API

A chave da API do TMDB está hardcoded no script:

```python
TMDB_API_KEY = "20c117664b56c63145516208a9dd5f5f"
```

Para alterar, edite a variável no arquivo `main.py`.

## Execução

### Execução Manual

```bash
# Ativar venv
source venv/bin/activate

# Executar
python3 main.py
```

### Saída de Exemplo

```
📥 Baixando planilha...
Colunas: ['Filmes']
Total de linhas: 150

[1/150] 🎬 The Matrix (1999)
  🎬 Buscando como filme...
  ✓ Filme encontrado: The Matrix (1999)
  ✓ 42 traduções encontradas
  📊 Obtendo detalhes em inglês...
  👥 Obtendo créditos em inglês...
     10 atores | 2 diretores
  💾 Traduções: /GitHub/Repos/Movie_Translations/Traduções/The_Matrix_1999_translations.json
  💾 Info (EN): /GitHub/Repos/Movie_Translations/Traduções/The_Matrix_1999_info.json

[2/150] 🎬 Breaking Bad (2008)
  🎬 Buscando como filme...
  📺 Buscando como série...
  ✓ Série encontrada: Breaking Bad (2008)
  ✓ 38 traduções encontradas
  ...

============================================================
✓ 6300 traduções exportadas
✓ 120 filmes processados
✓ 28 séries processadas
⚠ 2 itens pulados
============================================================
```

## Configuração como Serviço Systemd

O repositório inclui `movie-translations.service`. Para configurar:

```bash
# Criar link simbólico
sudo ln -s /caminho/absoluto/Movie_Translations/movie-translations.service /etc/systemd/system/

# Recarregar daemon
sudo systemctl daemon-reload

# Habilitar no boot
sudo systemctl enable movie-translations

# Iniciar serviço
sudo systemctl start movie-translations

# Verificar status
sudo systemctl status movie-translations

# Ver logs
sudo journalctl -u movie-translations -f
```

## Nomenclatura de Arquivos

### Filmes

- `The_Matrix_1999_translations.json`
- `The_Matrix_1999_translations.csv`
- `The_Matrix_1999_info.json`

### Séries (Prefixo `[SERIE]_`)

- `[SERIE]_Breaking_Bad_2008_translations.json`
- `[SERIE]_Breaking_Bad_2008_translations.csv`
- `[SERIE]_Breaking_Bad_2008_info.json`

## Idiomas Suportados

O sistema extrai **todos os idiomas disponíveis** no TMDB para cada filme/série. Idiomas comuns incluem:

pt-BR, en-US, es-ES, es-MX, fr-FR, de-DE, it-IT, ja-JP, ko-KR, zh-CN, zh-TW, ru-RU, ar-SA, hi-IN, pl-PL, nl-NL, sv-SE, tr-TR, th-TH, vi-VN, id-ID, e muitos outros.

## Rate Limiting

O script inclui delay de **0.3 segundos** entre requisições para respeitar limites da API do TMDB.

## Tratamento de Erros

- **Filme não encontrado**: Tenta como série automaticamente
- **Ano não bate**: Tenta sem ano como fallback
- **Sem traduções**: Pula item e continua
- **Erros de rede**: Exibe traceback e continua processamento

## Integração

Este módulo trabalha em conjunto com **Movie_Thumbnails** para fornecer solução completa de conteúdo multilíngue.

## Recursos da API

- **TMDB API Docs**: https://developers.themoviedb.org/3
- **Translations Endpoint**: https://developers.themoviedb.org/3/movies/get-movie-translations

## Notas Importantes

- ✅ Detalhes e créditos são **sempre em inglês** (`language=en-US`)
- ✅ Traduções incluem **todos os idiomas** disponíveis no TMDB
- ✅ Séries são marcadas com prefixo `[SERIE]_`
- ✅ Ano é validado entre planilha e resultado TMDB
- ✅ Top 10 atores ordenados por importância
