### Prompt umano 

Agisci come un esperto sviluppatore C# e crea un’applicazione Console avanzata, basata su .NET 8.0, per la gestione di una lista TODO con persistenza su SQLite.
L’applicazione deve utilizzare le librerie Microsoft.EntityFrameworkCore.Sqlite, Spectre.Console per l’interfaccia CLI, xUnit per i test e Microsoft.EntityFrameworkCore.InMemory per i test di repository e servizi.

L’architettura deve seguire un approccio pulito e modulare, basato sui pattern Repository, Dependency Injection, Code First ed elementi di Clean Architecture.

L’applicazione deve includere una serie di strumenti (“tools”) per la gestione delle attività, tra cui:

- creazione di un task

- lettura di tutti i task

- lettura per categoria

- lettura dei task scaduti

- lettura dei task pendenti

- toggle dello stato di completamento

- eliminazione

- ordinamento per data

Inoltre, deve essere presente un set di strumenti dedicati alle categorie, come la visualizzazione dell’elenco e l’aggiunta di nuove categorie.

La struttura del progetto deve essere organizzata nei seguenti file e cartelle:

- src/TodoApp.Console: Program.cs, README.md

- src/TodoApp.Domain: TodoItem.cs, Category.cs

- src/TodoApp.Data: TodoDbContext.cs

- src/TodoApp.Repositories: ITodoRepository.cs, TodoRepository.cs

- src/TodoApp.Services: TodoService.cs

- src/TodoApp.Cli: ConsoleUi.cs, TableRenderer.cs

- tests/TodoApp.Tests: TodoServiceTests.cs, TodoRepositoryTests.cs

Il database deve essere inizializzato tramite EnsureCreated().
Le date devono essere gestite tramite DateOnly.
L’interfaccia CLI deve utilizzare Spectre.Console, con rendering colorato: errori in rosso, warning per scadenze in giallo e task completati in verde.

## h2c

La catena completa è in [`todo-console.h2c`](todo-console.h2c) e passa `h2c validate`.

### 🔍 Comparazione  ***Copilot***

### 🎯 1. Equivalenza semantica

✔ **Identicità semantica: 100%**

### Token

H2C non è un formato di compressione: la catena porta stato esplicito e
costa più token di questo brief in linguaggio naturale. Numeri misurati in
[`conformance/Result.md`](../conformance/Result.md)
(`python3 conformance/benchmark.py fixtures`).