# Inteligentny konfigurator PC

## Projekt i odbiorcy

Konfigurator pomaga osobom skladajacym PC wybrac czesci oraz zrozumiec ich zgodnosc, koszt i kompromisy. Ma wspierac zarowno mniej doswiadczonych kupujacych, jak i osoby porownujace warianty zestawu.

## Cel docelowy i sukces

Docelowo uzytkownik buduje kompletny PC, otrzymuje wyjasniona ocene kompatybilnosci, bilansu i ceny oraz moze wrocic do udostepnionej konfiguracji. Sukces to aktualizowana baza produktow z x-kom, wiarygodna analiza wieloczynnikowa i uzyteczne porownanie ofert.

## Stan szkieletu

Stoi jedna dzialajaca sciezka: wybor CPU i plyty glownej w przegladarce, wywolanie API, obliczenie lacznej ceny oraz blokada przy niezgodnym sockecie. Regula jest wykonywana na serwerze Python; test uruchamia ten sam serwer i sprawdza odpowiedz API. Dane sa celowo przykadowe i lokalne.

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

Najpierw rozszerzyc model danych i analize do RAM, GPU i PSU wraz z testami reguly serwerowej, nastepnie dodac trwale dane oraz import produktu. Dopiero potem katalog, filtrowanie, oferty, zapis i warianty.

## Swiadomie odlozone

Nie ma jeszcze katalogu, importu, zewnetrznych cen, persystencji, kont, porownan, budzetu ani analiz poza socketem CPU-plyta. Nie sa to obietnice szkieletu ani dlug implementacyjny tego zadania.
