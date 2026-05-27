## Prompt umano 

Crea un progetto per una API meteo sviluppata in Python 3.11 utilizzando FastAPI.
Il progetto deve integrare le librerie FastAPI, httpx in modalità asincrona e cachetools.

L’autenticazione deve avvenire tramite API Key, letta dalla variabile d’ambiente OPENWEATHER_API_KEY.
L’API deve consumare i dati di OpenWeatherMap.

Organizza il progetto seguendo un pattern modulare basato su router e service.
Le funzionalità principali devono essere esposte come “tools” e includere due operazioni: current e forecast.

La struttura dei file deve essere la seguente:

- main.py

- routers/weather.py

- services/weather_service.py

- services/cache_service.py

- models/weather.py

- config.py

- .env

Implementa una cache in memoria con TTL pari a 10 minuti e un rate limit di 60 richieste al minuto.
Le chiamate HTTP verso OpenWeatherMap devono essere asincrone e realizzate tramite httpx.

L’API deve essere ben strutturata, modulare e facilmente estendibile.

## h2c 


[ARCH:PLAN]
id:api-meteo|fw:python3.11|lib:fastapi,httpx,cachetools|auth:APIKey::env(OPENWEATHER_API_KEY)|pattern:router,service|tools:[weather:{current,forecast}]|struct:[main.py,routers/weather.py,services/{weather_service.py,cache_service.py},models/weather.py,config.py,.env]|deps:OpenWeatherMap|notes:[cache_TTL_10min,rate-limit_60req-min,httpx_async]


### 🔍 Comparazione dettagliata **Copilot**

## Equivalenza semantica

Identicità semantica: 100%

## Mappatura 1:1 tra h2c e prompt umano

| Campo h2c | Contenuto nel prompt umano | Link |
|-----------|---------------------------|------|
| id:api-meteo | “Crea un progetto per una API meteo” | API meteo |
| fw:python3.11 | “sviluppata in Python 3.11” | Python 3.11 |
| lib:fastapi,httpx,cachetools | “utilizzando FastAPI, httpx async e cachetools” | Librerie |
| auth:APIKey::env(OPENWEATHER_API_KEY) | “API Key letta da OPENWEATHER_API_KEY” | API Key |
| pattern:router,service | “pattern modulare router + service” | Pattern router/service |
| tools:[weather:{current,forecast}] | “due operazioni: current e forecast” | Tools meteo |
| struct:[…] | “struttura dei file…” | Struttura progetto |
| deps:OpenWeatherMap | “consuma i dati di OpenWeatherMap” | OpenWeatherMap |
| note:cache TTL 10min | “cache TTL 10 minuti” | Cache TTL |
| note:rate-limit 60req/min | “rate limit 60 richieste/minuto” | Rate limit |
| note:httpx async | “chiamate HTTP asincrone tramite httpx” | httpx async |


### 🔍 Comparazione  ***Copilot***

### 🎯 1. Equivalenza semantica

✔ **Identicità semantica: 100%**

### Token stimati

- **Prompt umano** → ≈ 160–180 token
- **Output h2c** → ≈ 55–65 token

L'h2c utilizza circa il **35%** dei token rispetto al prompt umano.

### 🚀 Risparmio del 65% dei token.