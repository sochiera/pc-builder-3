## US-026 — Uzytkownik przeglada historie ceny konkretnej oferty [nowa]

Jako kupujacy chce zobaczyc chronologiczna historie ceny wybranej oferty sklepu, zeby ocenic jej trend bez mieszania cen roznych sprzedawcow.

- Dlaczego teraz: PROJECT.md wymaga historii cen, a raport weryfikacji nie potwierdzil jeszcze tej sekcji i dotychczasowa historyjka ogranicza sie do dwoch ostatnich pomiarow produktu.
- Sekcja briefu: Historia cen
- Sprawdzenie: otworz przygotowana oferte x-kom z co najmniej trzema zapisanymi pomiarami i sprawdz, ze widac nazwe sklepu oraz wszystkie daty i ceny w kolejnosci od najnowszej do najstarszej.
- Poza zakresem: wykres, alerty, statystyki, prognozowanie i laczenie historii ofert roznych sklepow.

## US-001 — Operator odswieza katalog x-kom [zrobiona]

Jako operator katalogu chce pobrac komplet aktualnie dostepnych produktow z x-kom i zobaczyc wynik importu, zeby uzytkownicy pracowali na aktualnej ofercie.

- Dlaczego teraz: PROJECT.md uznaje aktualizowana baze produktow z x-kom za warunek sukcesu i fundament katalogu.
- Sekcja briefu: Import wszystkich produktów z x-kom
- Sprawdzenie: uruchom import na przygotowanej odpowiedzi x-kom i sprawdz, ze raport pokazuje wszystkie zawarte w niej produkty oraz liczbe zaimportowanych pozycji.
- Poza zakresem: import przyrostowy, harmonogram i inne sklepy.

## US-002 — System rozpoznaje ten sam produkt [zrobiona]

Jako opiekun katalogu chce zobaczyc, ze dwie oferty tego samego modelu zostaly przypisane do jednego produktu, zeby ceny nie tworzyly duplikatow czesci.

- Dlaczego teraz: PROJECT.md rozdziela rozpoznane produkty od ofert sklepowych, wiec stabilna tozsamosc jest podstawa dalszych cen i porownan.
- Sekcja briefu: Identyfikacja produktów
- Sprawdzenie: wczytaj dwie przygotowane oferty tego samego modelu z roznymi nazwami i sprawdz, ze widac jeden produkt z dwiema ofertami.
- Poza zakresem: automatyczne rozstrzyganie niejednoznacznych dopasowan i laczenie calego historycznego katalogu.

## US-003 — Uzytkownik przeglada katalog [zrobiona]

Jako kupujacy chce zobaczyc liste dostepnych czesci z typem, modelem i cena, zeby rozpoczac wybor bez znajomosci konkretnego produktu.

- Dlaczego teraz: PROJECT.md wymaga katalogu opartego na odswiezalnych danych, ktory zasila konfigurator.
- Sekcja briefu: Lista produktów
- Sprawdzenie: otworz katalog po imporcie i sprawdz, ze widac po jednej przygotowanej czesci kazdego obslugiwanego typu wraz z modelem i cena.
- Poza zakresem: filtrowanie, wyszukiwanie, sortowanie i stronicowanie.

## US-004 — Uzytkownik sklada kompletny komputer [zrobiona]

Jako kupujacy chce wybrac po jednej czesci wymaganych typow i zobaczyc caly zestaw, zeby miec jedno miejsce do jego budowy.

- Dlaczego teraz: PROJECT.md definiuje kompletny PC obejmujacy CPU, plyte, RAM, GPU, dysk, PSU, chlodzenie i obudowe jako rdzen produktu.
- Sekcja briefu: Konfigurator
- Sprawdzenie: wybierz po jednej czesci osmiu typow i sprawdz, ze wszystkie widac w jednym zestawie, a zmiana dowolnej czesci odswieza wynik.
- Poza zakresem: wiele sztuk jednego typu, akcesoria i automatyczny dobor.

## US-005 — Uzytkownik widzi zaleznosc wielu czesci [zrobiona]

Jako skladajacy komputer chce zobaczyc wyjasnienie zaleznosci obejmujacej CPU, plyte i chlodzenie, zeby nie oceniac kazdej pary w oderwaniu.

- Dlaczego teraz: PROJECT.md wymaga zaleznosci wieloczynnikowych, a obecny szkielet sprawdza tylko socket pary CPU-plyta.
- Sekcja briefu: Zależności między komponentami
- Sprawdzenie: wybierz przygotowane CPU, plyte i chlodzenie, ktore dopiero razem tworza konflikt, i sprawdz, ze wynik wskazuje wszystkie trzy czesci oraz powod.
- Poza zakresem: drugi rodzaj zaleznosci wieloczynnikowej i automatyczna zamiana czesci.

## US-017 — Uzytkownik wybiera oferte innego sklepu [w toku]

Jako kupujacy chce przy rozpoznanym produkcie porownac oferte x-kom z oferta jednego innego sklepu i przejsc do wybranej, zeby kupic produkt w korzystniejszym miejscu.

- Dlaczego teraz: PROJECT.md przewiduje oferty innych sklepow dla rozpoznanych produktow, a mapa pokrycia wskazuje te sekcje jako nastepna do otwarcia.
- Sekcja briefu: Inne sklepy
- Sprawdzenie: otworz przygotowany rozpoznany produkt z oferta x-kom i drugiego sklepu, porownaj widoczne ceny, a nastepnie otworz kazdy link i sprawdz, ze prowadzi do wlasciwej oferty.
- Poza zakresem: kolejny sklep, koszt dostawy, automatyczne wyszukiwanie ofert i optymalizacja koszyka.

## US-023 — Uzytkownik znajduje oferte w innym sklepie [zrobiona]

Jako kupujacy chce wyszukac oferte innego sklepu dla rozpoznanego produktu, zeby porownanie nie bylo ograniczone do ofert dostarczonych podczas importu x-kom.

- Dlaczego teraz: PROJECT.md przewiduje oferty innych sklepow dla rozpoznanych produktow, a US-017 potwierdzila jedynie obsluge juz przygotowanej oferty i nadal czeka na pelny dowod.
- Sekcja briefu: Inne sklepy
- Sprawdzenie: uruchom wyszukiwanie dla przygotowanego rozpoznanego produktu majacego poczatkowo tylko oferte x-kom i sprawdz, ze pojawia sie dopasowana oferta drugiego sklepu z jego nazwa, cena i linkiem.
- Poza zakresem: nierozpoznane produkty, trzeci sklep, koszt dostawy, automatyczny harmonogram i optymalizacja koszyka.

## US-006 — Uzytkownik sprawdza kompatybilnosc zestawu [zrobiona]

Jako kupujacy chce po kazdej zmianie zobaczyc, czy caly zestaw jest zgodny oraz dlaczego, zeby nie kupic czesci, ktorych nie da sie polaczyc.

- Dlaczego teraz: PROJECT.md stawia wyjasniona ocene kompatybilnosci jako glowny wynik konfiguratora.
- Sekcja briefu: Kompatybilność
- Sprawdzenie: zmien zgodna plyte na model z innym socketem i sprawdz, ze ocena zestawu natychmiast zmienia sie na niezgodna z wyjasnieniem.
- Poza zakresem: wydajnosc, cena i rekomendowanie zamiennikow.

## US-007 — Uzytkownik rozroznia wage problemow [zrobiona]

Jako kupujacy chce widziec osobno blokady, ostrzezenia i informacje z uzasadnieniem, zeby wiedziec, co musze poprawic, a co tylko rozwazyc.

- Dlaczego teraz: PROJECT.md wprost wymaga trzech poziomow analizy z jasnym uzasadnieniem.
- Sekcja briefu: Poziomy problemów
- Sprawdzenie: otworz przygotowany zestaw zawierajacy po jednym komunikacie kazdego poziomu i sprawdz ich odrebne oznaczenie oraz tresc uzasadnienia.
- Poza zakresem: konfigurowalne poziomy, ukrywanie komunikatow i ranking problemow.

## US-008 — Uzytkownik widzi niepewna ocene danych [zrobiona]

Jako kupujacy chce zostac ostrzezony, gdy brakuje danych albo dane sobie przecza, zeby brak informacji nie wygladal jak potwierdzona zgodnosc.

- Dlaczego teraz: PROJECT.md zabrania traktowania braku danych jako automatycznej zgodnosci.
- Sekcja briefu: Brakujące lub sprzeczne dane
- Sprawdzenie: otworz przygotowany zestaw raz z brakujacym parametrem, a raz ze sprzecznymi wartosciami, i sprawdz, ze w obu przypadkach ocena pozostaje nierozstrzygnieta z podanym powodem.
- Poza zakresem: automatyczne uzupelnianie danych i panel korekty katalogu.

## US-009 — Uzytkownik sprawdza zgodnosc RAM [zrobiona]

Jako skladajacy komputer chce zobaczyc, czy wybrana pamiec RAM pasuje do plyty i CPU, zeby uniknac nieobslugiwanej pamieci.

- Dlaczego teraz: PROJECT.md wskazuje RAM jako pierwszy kierunek rozszerzenia analizy poza socket.
- Sekcja briefu: Analiza RAM
- Sprawdzenie: wybierz przygotowany modul o nieobslugiwanym standardzie i sprawdz, ze analiza wskazuje konflikt RAM z plyta oraz uzasadnienie.
- Poza zakresem: taktowania, profile podkrecania, opoznienia i konfiguracje wielu modulow.

## US-010 — Uzytkownik sprawdza zapas zasilania [zrobiona]

Jako skladajacy komputer chce zobaczyc, czy moc PSU wystarcza dla wybranego zestawu, zeby nie kupic zbyt slabego zasilacza.

- Dlaczego teraz: PROJECT.md wskazuje PSU i wiarygodny bilans jako elementy pierwszego rozszerzenia analizy.
- Sekcja briefu: Analiza zasilania
- Sprawdzenie: wybierz przygotowany zestaw przekraczajacy moc PSU i sprawdz, ze analiza pokazuje wymaganie, dostepna moc i blokade.
- Poza zakresem: sprawnosc, okablowanie, skoki poboru i rekomendowany zapas procentowy.

## US-011 — Uzytkownik okresla przeznaczenie komputera [zrobiona]

Jako kupujacy chce wybrac jedno zastosowanie komputera, zeby oceny zestawu odnosily sie do mojego celu.

- Dlaczego teraz: PROJECT.md wymaga obslugi przeznaczenia i ocen zaleznych od zastosowania.
- Sekcja briefu: Przeznaczenie komputera
- Sprawdzenie: wybierz przygotowane zastosowanie i sprawdz, ze jest widoczne przy zestawie oraz uwzglednione w jego ocenie.
- Poza zakresem: laczenie zastosowan, wlasne profile i szczegolowe wymagania programow.

## US-012 — Uzytkownik pilnuje budzetu [zrobiona]

Jako kupujacy chce podac maksymalny budzet i zobaczyc, ile zostalo albo o ile zestaw go przekracza, zeby kontrolowac koszt podczas zmian.

- Dlaczego teraz: PROJECT.md wymienia budzet jako podstawowy kontekst decyzji zakupowej.
- Sekcja briefu: Budżet
- Sprawdzenie: ustaw budzet ponizej ceny zestawu, a potem zmien czesc na tansza, i sprawdz aktualizacje kwoty przekroczenia albo pozostalego budzetu.
- Poza zakresem: osobne limity kategorii, waluty i raty.

## US-013 — Uzytkownik ocenia bilans zestawu [zrobiona]

Jako kupujacy chce zobaczyc jedna wyjasniona ocene zestawu dla wybranego zastosowania, zeby rozpoznac jego najslabszy element.

- Dlaczego teraz: PROJECT.md uznaje wiarygodna analize wieloczynnikowa i wyjasniona ocene bilansu za kryteria sukcesu.
- Sekcja briefu: Ocena zestawu
- Sprawdzenie: otworz przygotowany niezbalansowany zestaw i sprawdz, ze ocena wskazuje jego najslabszy element oraz zwiazek z wybranym zastosowaniem.
- Poza zakresem: wiele metryk punktowych, benchmarki i rekomendacje zamiennikow.

## US-014 — Uzytkownik znajduje najtanszy zestaw [zrobiona]

Jako kupujacy chce otrzymac najtanszy zgodny zestaw dla jednego zastosowania i budzetu, zeby miec prosty punkt wyjscia do zakupu.

- Dlaczego teraz: PROJECT.md ma pomagac mniej doswiadczonym kupujacym wybrac czesci przy uwzglednieniu zgodnosci, kosztu i kompromisow.
- Sekcja briefu: Najtańszy zestaw
- Sprawdzenie: wybierz zastosowanie i budzet dla przygotowanego katalogu, uruchom dobor i sprawdz, ze pokazany kompletny zgodny zestaw jest najtanszy z dostepnych kombinacji.
- Poza zakresem: kilka propozycji, optymalizacja wydajnosci i zakupy w wielu sklepach.

## US-015 — Uzytkownik odnajduje produkt [zrobiona]

Jako kupujacy chce wyszukac model i ograniczyc katalog do jednego typu czesci, zeby szybko dotrzec do interesujacego produktu.

- Dlaczego teraz: PROJECT.md odklada filtrowanie do czasu powstania katalogu, ktory zapewniaja wczesniejsze historyjki.
- Sekcja briefu: Filtrowanie i wyszukiwanie
- Sprawdzenie: wpisz fragment nazwy przygotowanego GPU, wlacz filtr GPU i sprawdz, ze lista zawiera pasujacy model oraz nie pokazuje pozostalych typow.
- Poza zakresem: drugi filtr, podpowiedzi, tolerowanie literowek i sortowanie.

## US-016 — Uzytkownik odswieza ceny produktu [zrobiona]

Jako kupujacy chce uruchomic wyszukanie aktualnych ofert dla wybranego produktu i zobaczyc czas sprawdzenia, zeby decyzja nie opierala sie na starej cenie.

- Dlaczego teraz: PROJECT.md wymaga uzytecznego porownania ofert i aktualnych danych cenowych.
- Sekcja briefu: Wyszukiwanie cen
- Sprawdzenie: uruchom wyszukanie dla przygotowanego produktu i sprawdz, ze widac odnaleziona cene oraz czas ostatniego sprawdzenia.
- Poza zakresem: automatyczny harmonogram, powiadomienia i historia zmian.

## US-018 — Uzytkownik porownuje dwa komponenty [nowa]

Jako kupujacy chce zestawic dwa komponenty tego samego typu obok siebie, zeby zobaczyc roznice ceny i kluczowego parametru.

- Dlaczego teraz: PROJECT.md wskazuje porownania jako potrzebne osobom rozwazajacym alternatywy.
- Sekcja briefu: Porównywanie komponentów
- Sprawdzenie: wybierz dwa przygotowane GPU i sprawdz, ze widac obok siebie ich nazwy, ceny i jeden kluczowy parametr z zaznaczonymi roznicami.
- Poza zakresem: trzeci produkt, dowolne parametry i porownanie zestawow.

## US-024 — Uzytkownik porownuje zamienniki w zestawie [zrobiona]

Jako kupujacy chce porownac dwa zamienniki dla jednego miejsca w aktualnym zestawie, zeby przed zmiana zobaczyc wplyw kazdego na zgodnosc i laczna cene konfiguracji.

- Dlaczego teraz: PROJECT.md wskazuje porownania i kompromisy jako potrzebe osob rozwazajacych warianty, a dowod US-018 nie potwierdzil jeszcze porownania w dzialajacej przegladarce.
- Sekcja briefu: Porównywanie komponentów
- Sprawdzenie: w przygotowanym kompletnym zestawie porownaj dwie plyty glowne, z ktorych jedna pasuje do CPU, a druga nie, i sprawdz obok siebie wynik zgodnosci z uzasadnieniem oraz laczna cene zestawu dla kazdej opcji.
- Poza zakresem: zastosowanie zamiennika do zestawu, porownanie wiecej niz dwoch opcji i automatyczna rekomendacja lepszej czesci.

## US-025 — Uzytkownik porownuje oplacalnosc komponentow [zrobiona]

Jako kupujacy chce porownac koszt i przydatnosc dwoch komponentow dla wybranego zastosowania, zeby swiadomie zdecydowac, czy drozsza opcja daje mi istotna korzysc.

- Dlaczego teraz: PROJECT.md wskazuje porownania, koszt i kompromisy jako podstawe decyzji osob wybierajacych czesci, a istniejace historyjki nie lacza porownania komponentow z przeznaczeniem komputera.
- Sekcja briefu: Porównywanie komponentów
- Sprawdzenie: wybierz Gaming oraz dwa przygotowane GPU o roznej cenie i przydatnosci, a nastepnie sprawdz, ze porownanie pokazuje dla obu cene, ocene dla Gaming i wyjasnienie roznicy.
- Poza zakresem: automatyczny wybor zwyciezcy, benchmarki zewnetrzne, porownanie calego zestawu i wiecej niz dwa komponenty.

## US-019 — Uzytkownik tworzy wariant zestawu [zrobiona]

Jako kupujacy chce skopiowac zestaw do jednego wariantu i zmienic w nim czesc, zeby zachowac punkt odniesienia podczas rozwazania alternatywy.

- Dlaczego teraz: PROJECT.md wymaga wariantow dla osob porownujacych kompromisy zestawu.
- Sekcja briefu: Warianty zestawu
- Sprawdzenie: skopiuj przygotowany zestaw, zmien GPU w kopii i sprawdz, ze wariant bazowy pozostal bez zmian, a oba maja widoczne laczne ceny.
- Poza zakresem: trzeci wariant, automatyczne generowanie i scalanie zmian.

## US-020 — Uzytkownik zapisuje konfiguracje [zrobiona]

Jako kupujacy chce zapisac aktualny zestaw i ponownie go otworzyc, zeby nie utracic wykonanej pracy po zamknieciu aplikacji.

- Dlaczego teraz: PROJECT.md wymaga mozliwosci powrotu do konfiguracji i trwalych danych.
- Sekcja briefu: Zapis konfiguracji
- Sprawdzenie: zapisz przygotowany zestaw, zamknij i ponownie uruchom aplikacje, a nastepnie otworz go i sprawdz czesci, budzet oraz przeznaczenie.
- Poza zakresem: konta, synchronizacja miedzy urzadzeniami i wersjonowanie zapisu.

## US-021 — Uzytkownik udostepnia konfiguracje [zrobiona]

Jako kupujacy chce utworzyc link do zapisanego zestawu, zeby druga osoba mogla go otworzyc bez dostepu do mojego urzadzenia.

- Dlaczego teraz: PROJECT.md definiuje powrot do udostepnionej konfiguracji jako czesc celu produktu.
- Sekcja briefu: Udostępnianie
- Sprawdzenie: utworz link do przygotowanego zapisanego zestawu i otworz go w nowej sesji, sprawdzajac zgodnosc czesci i podsumowania ceny.
- Poza zakresem: edycja przez odbiorce, prywatne linki, wygasanie i media spolecznosciowe.

## US-022 — Uzytkownik sprawdza historie ceny [w toku]

Jako kupujacy chce zobaczyc ostatnia i poprzednia cene wybranego produktu, zeby ocenic, czy obecna oferta spadla czy wzrosla.

- Dlaczego teraz: PROJECT.md wymaga historii cen, ale najciensza wersja wystarczy do pokazania kierunku zmiany.
- Sekcja briefu: Historia cen
- Sprawdzenie: otworz przygotowany produkt z dwoma zapisanymi pomiarami i sprawdz, ze widac obie daty, ceny oraz kierunek zmiany.
- Poza zakresem: wykres, alerty, statystyki i wiecej niz dwa pomiary.
