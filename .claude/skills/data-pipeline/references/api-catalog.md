# API & Data Source Catalog

Known sources for quiz data, tested and working.

## Audio

| Source | URL | Auth | Notes |
|--------|-----|------|-------|
| iTunes Search | `https://itunes.apple.com/search?term=...&media=music&limit=25` | None | 30s previews, m4a format, URLs expire in ~24h |
| Freesound | `https://freesound.org/apiv2/` | API key | Sound effects, ambient, CC-licensed |

## Characters / Relationships

| Source | URL | Auth | Notes |
|--------|-----|------|-------|
| PokeAPI | `https://pokeapi.co/api/v2/` | None | Full Pokédex, evolutions, types, stats |
| SWAPI | `https://swapi.dev/api/` | None | Star Wars characters, films, planets |
| HP API | `https://hp-api.onrender.com/api/` | None | Harry Potter characters, houses |
| TMDB | `https://api.themoviedb.org/3/` | API key | Movies, TV, cast, crew relationships |
| MusicBrainz | `https://musicbrainz.org/ws/2/` | None (rate limited) | Artists, collaborations, releases |

## Geography

| Source | URL | Auth | Notes |
|--------|-----|------|-------|
| REST Countries | `https://restcountries.com/v3.1/` | None | Borders, capitals, regions, populations |
| Natural Earth | naturalearthdata.com | None (download) | Shapefiles for borders, coastlines |

## Sports

| Source | URL | Auth | Notes |
|--------|-----|------|-------|
| Football-Data | `https://www.football-data.org/v4/` | Free tier key | Leagues, teams, players, standings |
| NBA API | `https://www.balldontlie.io/api/v1/` | None | Players, teams, stats |
| Ergast F1 | `https://ergast.com/api/f1/` | None | Drivers, constructors, races, results |

## General Knowledge

| Source | URL | Auth | Notes |
|--------|-----|------|-------|
| Wikidata | `https://query.wikidata.org/sparql` | None | Anything with SPARQL queries |
| Open Trivia DB | `https://opentdb.com/api.php` | None | Pre-made trivia questions, categories |

## Tips

- Always check rate limits before batch-fetching
- Cache responses locally during development (`json.dump` to file)
- Wikipedia/Wikidata is best for relationship data (co-occurrence, shared attributes)
- For network quizzes, aim for 30-150 nodes and 2-5x edges-to-nodes ratio
