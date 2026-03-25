# Un Giorno in Universita` 2026

### ADMStaff lab - https://students.cs.unibo.it

### Scoreboard live: https://ugu.students.cs.unibo.it/scoreboard

Ciao! Benvenuti al laboratorio di orientamento organizzato da ADMStaff :)

Qui troverete alcune info utili per utilizzare i file presenti in questa cartella
e mettervi alla prova per giocare insieme con l'informatica.

## Files

- `README.md`: questo file, con tutte le istruzioni per giocare.
- `exploit_client.py`: è il client che userete per connettervi a un team avversario, rispondere al quiz e risolvere i 3 step.
- `team_server.py`: è il server del vostro team in cui verranno elaborati gli step che implementerete sul client. Non dovete modificare questo file, ma è utile per capire come funziona il sistema.
- `lib/`: ignorate questa cartella, contiene solo librerie di supporto per il client e il server per comunicare e validare le flag con il server validator centrale.
- `ugu-2026.pdf`: è il pdf con le slide che abbiamo mostrato prima.

## 1. Avvio team_server

Prima di avviare il server del team, dovrete trovare il vostro ip e impostarlo nel file `team_server.py` alla riga 11:

```python
HOST = "0.0.0.0" # Sostituite con l'IP reale del vostro team
```

per trovare il votro ip usate il comando `ip a` e cercate l'ip associato alla vostra interfaccia di rete (di solito `eth0` o `wlan0`).

A questo punto potrete avviare il server del vostro team, per registrarvi al sistema, verrà poi mostrato sul monitor il vostro nome con l'ip, si aggiornerà poi man mano che risolverete gli step:

```bash
TEAM_ID=<nome_team> TEAM_SERVER_PORT=5000 python3 team_server.py
```

## 2. Completamento step

Il vostro obiettivo è quello di completare `exploit_client.py` per risolvere gli step:
man mano che risolverete uno step otterrete una flag, che verrà inviata al validator centrale e vi verranno assegnati i punti.

Per eseguire il client, usate:

```bash
python3 exploit_client.py --host <IP_TEAM_AVVERSARIO> --port 5000 --validator --my-team <nome_team> --victim <team_avversario>
```

con questo comando una volta ottenuta la flag, questa verrà inviata al validator centrale per ottenere i punti automaticamente! Nel giro di massimo 5 secondi vedrete i punti aggiornati nella classifica sul monitor.

Per risolvere gli step, è utile connettersi al server per vedere cosa succede, e poi implementare la logica per risolvere i quiz.

per farlo potete usare `netcat`:

```bash
nc <IP_TEAM_AVVERSARIO> 5000
```

## 3. Rispondere al quiz

Per ogni step, il server del team avversario vi farà una domanda, e voi dovrete rispondere correttamente per ottenere la flag.

Quindi se riuscirete a vedere la domanda, sarete riuscitia a risolvere lo step.

- Quando compare `risposta>`, scrivete la risposta esatta.
- Il confronto è preciso: maiuscole/minuscole e spazi contano.
- Se sbagliate, potete riprovare finché non è corretta.

## 4. Invio flag manualmente al validator

Se volete, potete anche inviare le flag manualmente al validator centrale, senza usare l'opzione `--validator` del client, in questo modo potete vedere subito la flag ottenuta senza aspettare che il client la invii.
Il client stampa le flag, ma i punti si assegnano quando inviate la flag al validator.

Comando (ripetere per ogni flag):

```bash
curl -s -X POST https://ugu.students.cs.unibo.it/submit \
  -H 'Content-Type: application/json' \
  -d '{"team":"<nome_team>","victim":"<team_avversario>", "step":"<STEP>", "flag":"<FLAG>"}'
```

## Errori comuni

- `0.0.0.0` come host target NON va usato per connettersi.
    - Usate l'IP reale del team avversario: lo trovate sul monitor o chiedete ai ragazzi di ADMStaff.
    - Per test locale usate `127.0.0.1`.
- Se vedete `Unknown team`, controllate che il nome del team sia scritto uguale a quello registrato sul monitor.
- Se vedete `Invalid flag`, controllate di inviare la flag giusta e il `victim` giusto.

## Note utili

- Se avete dubbi durante la gara, chiedete ai ragazzi di ADMStaff prima di fare tentativi a caso.
