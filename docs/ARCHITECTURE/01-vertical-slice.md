# Pionowy szkielet

`app.py` zawiera lokalne dane CPU i plyt, funkcje `analyse`, endpoint API oraz serwowanie strony. Przegladarka przekazuje tylko identyfikatory wyborow do `GET /api/analyse`; nie oblicza kompatybilnosci samodzielnie. Ta sama funkcja tworzy odpowiedz, ktora sprawdza `test_app.py` po uruchomieniu procesu aplikacji na wolnym porcie.

Pierwsza regula porownuje socket CPU z socketem plyty, tworzy blokade z wyjasnieniem i sumuje ceny wybranych czesci. Uzycie standardowej biblioteki Pythona ogranicza bootstrap do jednego polecenia i nie jest decyzja o docelowym stosie produktu.
