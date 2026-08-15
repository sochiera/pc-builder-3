# Inteligentny konfigurator PC

## Projekt i odbiorcy

Konfigurator pomaga osobom skladajacym PC wybrac czesci oraz zrozumiec ich zgodnosc, koszt i kompromisy. Ma wspierac zarowno mniej doswiadczonych kupujacych, jak i osoby porownujace warianty zestawu.

## Cel docelowy i sukces

Docelowo uzytkownik buduje kompletny PC, otrzymuje wyjasniona ocene kompatybilnosci, bilansu i ceny oraz moze wrocic do udostepnionej konfiguracji. Sukces to aktualizowana baza produktow z x-kom, wiarygodna analiza wieloczynnikowa i uzyteczne porownanie ofert.

## Stan produktu

Dziala pelna lokalna sciezka kupujacego: import i przegladanie katalogu, budowa kompletnego zestawu, analiza zgodnosci, RAM, zasilania i bilansu, budzet, przeznaczenie, automatyczny dobor, porownania oraz warianty. Uzytkownik moze odswiezac i porownywac oferty, przegladac historie ceny konkretnej oferty, zapisac konfiguracje i udostepnic ja linkiem. Zakres zostal potwierdzony zewnetrznymi probami przegladarkowymi i API; nierozliczone, wezsze historyjki zostaly zastapione potwierdzonymi zdolnosciami o szerszym zakresie.

## Wymagania

- Konfigurator ma ponownie analizowac zestaw po zmianie czesci.
- Analiza ma rozrozniac blokady, ostrzezenia i informacje z jasnym uzasadnieniem.
- Docelowy zakres obejmuje CPU, plyte, RAM, GPU, dyski, PSU, chlodzenie i obudowe oraz zaleznosci wieloczynnikowe.
- Katalog x-kom ma byc odswiezalny; oferty innych sklepow dotycza juz rozpoznanych produktow.
- Aplikacja ma obslugiwac budzet, przeznaczenie, porownania, zapis, linki, warianty i historie cen.
- Brak danych nie moze oznaczac automatycznej zgodnosci.

## Preferencje

- Ton ma byc rzeczowy, pomocny i konkretny; komunikaty wyjasniaja decyzje zamiast tylko oznaczac status.
- Interfejs ma stawiac czytelnosc zestawu i decyzji ponad gestosc katalogu.
- Priorytetem jest pionowa, przetestowana funkcja przed rozbudowa kolejnych warstw.

## Pomysly opcjonalne

- Optymalizacja koszyka miedzy sklepami z kosztem dostawy.
- Rekomendacje oszczednosci i ocena oplacalnosci zalezne od zastosowania.

## Kolejnosc rozwoju

Zakres podstawowego briefu jest domkniety. Nie otwieramy kolejnych wariantow istniejacych funkcji bez nowego dowodu problemu uzytkownika albo zmiany briefu. Ewentualny dalszy rozwoj powinien zaczac sie od walidacji jednego z pomyslow opcjonalnych.

## Swiadomie odlozone

Konta, synchronizacja miedzy urzadzeniami, optymalizacja koszyka wielu sklepow, alerty cenowe i prognozowanie nie naleza do zakonczonego zakresu. Kryterium ukonczenia i opis testowania sa kontekstem procesu, a nie zdolnosciami uzytkownika. Podsumowanie jest widocznym wynikiem produktu, lecz nie wymaga osobnej historyjki: potwierdzona US-013 pokazuje wyjasniona ocene zestawu, a US-021 potwierdza podsumowanie ceny takze po otwarciu udostepnionej konfiguracji.
