# Programowanie sieciowe - PSI

## Laboratoria
### Zadanie 1
Napisz zestaw dwóch programów – klienta i serwera wysyłające dwukierunkowo datagramy UDP. Serwer obsługuje klientów z adresami IPv4 i IPv6. Wykonaj ćwiczenie w kolejnych inkrementalnych wariantach (rozszerzając kod z poprzedniej wersji).

#### Zadanie 1.1
Klient wysyła, a serwer odbiera datagramy o stałym, niewielkim rozmiarze (rzędu kilkudziesięciu bajtów). Datagramy mogą zawierać ustalony „na sztywno” lub generowany napis – np. „abcde….”, „bcdef…​”, itd. Powinno być wysyłanych kilka datagramów, po czym klient powinien kończyć pracę. Serwer raz uruchomiony pracuje aż do zabicia procesu.

Wykonać program w dwóch wariantach: C oraz Python.

Sprawdzić i przetestować działanie „między platformowe”, tj. klient w C z serwerem Python i vice versa.

#### Zadanie 1.2
Na bazie wersji 1.1 napisać klienta, który wysyła kolejne datagramy o wielkości będącej kolejnymi potęgami 2, tj. 1, 2, 4, 8, 16, itd. bajtów. Sprawdzić jaki był maksymalny rozmiar wysłanego (przyjętego) datagramu. Wyjaśnić.

### Zadanie 2
Napisz zestaw dwóch programów – klienta i serwera wysyłające dwukierunkowo dane w protokole TCP. Serwer obsługuje klientów z adresami IPv4 i IPv6.Wykonaj ćwiczenie w kolejnych inkrementalnych wariantach (rozszerzając kod z poprzedniej wersji). W wariancie Python należy początkowo w kodzie klienta i serwera użyć funkcji sendall().

#### Zadanie 2.1
Klient wysyła, serwer odbiera porcje danych o stałym, niewielkim rozmiarze (rzędu kilkudziesięciu bajtów). Mogą one zawierać ustalony „na sztywno” lub generowany napis – np. „abcde….”, „bcdef…​”, itd. Po wysłaniu danych klient powinien kończyć pracę. Serwer raz uruchomiony pracuje aż do zabicia procesu.

Wykonać program w dwóch wariantach: C oraz Python.

Sprawdzić i przetestować działanie „między platformowe”, tj. klient w C z serwerem Python i vice versa.

#### Zadanie 2.2
Zmodyfikować program serwera tak, aby bufor odbiorczy był mniejszy od wysyłanej jednorazowo przez klienta porcji danych. W wariancie Python wykonać eksperymenty z funkcjami send() i sendall(). Jak powinien zostać zmodyfikowany program klienta i serwera aby poprawnie obsłużyć komunikację? (uwaga – w zależności od wykonanej implementacji programu z punktu 2.1 mogą ale nie muszą poprawnie obsługiwać wariant transmisji z punktu 2.2).

#### Zadanie 2.3
Python – posługując się funkcją settimeout() zmodyfikować program z Z 2.1 tak, aby obsługiwał timeout-y dla funkcji connect() i accept().  

C – zrealizować timeout dla accept() korzystając z funkcji select(); zrealizowac connect() w wersji nieblokującej.

## Projekt - System niezawodnego strumieniowania danych po UDP.
Zaprojektuj i zaimplementuj protokół warstwy sesji, umożliwiający równoległe przesyłanie do 8 jednokierunkowych strumieni paczek danych stemplowanych czasem. Należy użyć protokołu UDP. Serwer powinien obsługiwać klientów o adresach IPv4 i IPv6. Można użyć implementacji protokołu TFTP (Trivial File Transfer Protocol).
