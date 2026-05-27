# Esempio H2C v1.2: Catena con PRUNE e COMPACT

Catena completa che mostra l'uso dei blocchi di contesto e di un ciclo di fix.

---

[ARCH:PLAN]
id:demo|fw:python3.11|lib:fastapi,sqlite,jwt,redis|pattern:rest_api_autenticata|notes:[user_model,jwt_auth,protected_routes,user_crud]

[BUILD:EXEC]
id:m1|target:main.py|desc:setup_fastapi_app

[BUILD:DONE]
id:m1|diff:[main.py~1]|rev:1

[BUILD:EXEC]
id:m2|target:models.py|desc:user_model|after:m1

[BUILD:DONE]
id:m2|diff:[models.py~1]|rev:1

[BUILD:EXEC]
id:m3|target:auth.py|desc:jwt_auth|after:m2

[CTX:PRUNE]
keep:last_5|pruned:[]

[BUILD:DONE]
id:m3|diff:[auth.py~1]|rev:1

[BUILD:EXEC]
id:m4|target:routes.py|desc:protected_routes|after:m3

[BUILD:DONE]
id:m4|diff:[routes.py~1]|rev:1

[TEST:RUN]
id:t1|cmd:pytest test_auth.py

[TEST:PASS]
id:t1|pass_count:5

[CTX:PRUNE]
keep:[m3,m4,t1]|pruned:[m1,m2]

[CTX:UPDATE]
~progress:layer=auth|status=done
~next:database
~active_files:[main.py~1,models.py~1,auth.py~1,routes.py~1]

[BUILD:EXEC]
id:m5|target:database.py|desc:sqlite_setup|after:m2

[BUILD:DONE]
id:m5|diff:[database.py~1]|rev:1

[BUILD:EXEC]
id:m6|target:crud.py|desc:user_crud|after:m5

[BUILD:DONE]
id:m6|diff:[crud.py~1]|rev:1

[TEST:RUN]
id:t2|cmd:pytest test_crud.py

[TEST:FAIL]
id:t2|error:crud.py:42:unique_constraint|cycle_id:fix-duplicate-email|fail_count:1|pass_count:4

[CTX:PRUNE]
keep:[m5,m6,t2]|pruned:[m3,m4,t1]

[BUILD:FIX]
id:f1|target:crud.py|base_rev:1|desc:handle_duplicate_email|cycle_id:fix-duplicate-email|retry_n:1

[BUILD:DONE]
id:f1|diff:[crud.py~2]|rev:2|cycle_id:fix-duplicate-email

[TEST:RUN]
id:t3|cmd:pytest test_crud.py

[TEST:PASS]
id:t3|pass_count:5|cycle_id:fix-duplicate-email

[CTX:PRUNE]
keep:[t2,f1,t3]|pruned:[m5,m6]

[CTX:COMPACT]
summary:[auth_done|crud_done|files:[main.py~1,models.py~1,auth.py~1,routes.py~1,database.py~1,crud.py~2]]
keep_active:[main.py~1,auth.py~1,routes.py~1,crud.py~2]
pruned_history:msg_1_to_20

[ORCH:END]
final:complete|est_token:62|pass_count:5|fail_count:1