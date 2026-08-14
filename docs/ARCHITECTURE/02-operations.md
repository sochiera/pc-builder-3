# Operacje

- Uruchomienie lokalne: `make run`, nastepnie `http://127.0.0.1:8000`.
- Smoke: `make smoke` uruchamia aplikacje i sprawdza stronke oraz konflikt socketu przez HTTP.
- CI: `make ci` jest aktualnie aliasem smoke, poniewaz istnieje tylko jedna pionowa sciezka.
- Hardware: `make hardware` jest aktualnie aliasem smoke; brak integracji sprzetowych nie wymaga dodatkowego testu.

Polecenia nalezy rozszerzac wraz z realnym zakresem, bez zastępowania testu integracyjnego testem zduplikowanej logiki.
