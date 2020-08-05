# Dokumentation Kalender-Skill

## Aufgabenstellung

Ziel der Mycroft-Aufgabe war es, einen Skill zu erstellen, mit welchem man aus seinem eigenen Kalender den zeitlich nächsten Termin über Spracheingabe abfragen kann. Optionale Funktionen des Skills sollten das Erstellen, Umbenennen und Löschen eines Kalendereintrags und alle Einträge an einem bestimmten Tag sein.  

## Mycroft installieren

Für die Installation von Mycroft wird ein Linux Betriebssystem benötigt. Ist man Windows oder MacOS Nutzer, muss man eine Virtual Machine mit einem Linux/ Ubuntu Image installieren (z.B. VirtualBox). Zusätzlich wird ein Mikrofon und ein Lautsprecher für die Ein-/ Ausgabe benötigt.  
Mithilfe der Dokumentation auf der Seite https://mycroft-ai.gitbook.io/docs/using-mycroft-ai/get-mycroft kann man Mycroft installieren. Dabei werden die benötigten Packages mitinstalliert oder gegebenenfalls aktualisiert. Nach einer erfolgreichen Installation lässt sich in dem neu erstellten Mycroft-Verzeichnis mit dem Befehl ./start-mycroft.sh das Programm starten. Fügt man zusätzlich noch ein "debug" an das Ende des Befehls, kann man das Programm überwachen.  
Für den nächsten Schritt wird ein Account bei Mycroft benötigt, diesen kann man auf der Seite https://mycroft.ai/ erstellen. Nach dem initialem Start von Mycroft muss man das Programm mit seinem Account verbinden. Dafür folgt man der Dokumentation auf der Seite https://mycroft-ai.gitbook.io/docs/using-mycroft-ai/pairing-your-device. Sobald eine Verbindung besteht, kann man Mycroft verwenden.  

## Einen neuen Skill erstellen

Für das Erstellen eines neuen Mycroft-Skills eignet sich sehr gut die Dokumentation auf der Seite https://mycroft-ai.gitbook.io/docs/skill-development/introduction/your-first-skill.  
Hier wird auf das Mycroft-Skill-Kit verwiesen (https://mycroft-ai.gitbook.io/docs/mycroft-technologies/mycroft-skills-kit), welches bereits mit der Installation von Mycroft mitinstalliert wird. Mithile dieses Kits und dem dazugehörigen Command "mycroft-msk create", wird eine interactive Erstellung eines neuen Skills gestartet. Es wird dabei Name, Github Repository und Beschreibung des neuen Skills festgelegt und anschließend wird ein leeres Skill Template angelegt. Nach erfolgreichem Anlegen, kann man seinen neuen Skill unter dem Verzeichnis "/mycroft/skills" finden. 

## Appointment-Skill

Der Skill besteht aus 3 wesentlichen Bestandteilen

1. Einem Python Skript "\_\_init__.py", in welchem die Logik des Skill ist:  
Das Skript besteht aus einer Skill-Klasse mit verschieden Methoden, die über ihre "Intents" von Mycroft aufgerufen werden.
2. Den Intents:  
Die Intent sind "Trigger" Sätze für die Methoden des Skills. Jede Funktion des Skills wird mit einem Intent gekennzeichnet. Sobald der User an Satz an Mycroft spricht, der mit einem Intent übereinstimmt, wird diese Methode aufgerufen.
3. Die Dialoge:  
Dialoge sind die Ausgaben von Mycroft. Sie können mit Daten aus den Methoden des Skills angereichert werden.

### CalDAV Funktion

Für den Appointment-Skill habe ich als Erstes eine passende Bibliothek von Python gesucht, mit welcher man auf einen Kalender zugreifen kann. Meine Wahl fiel auf die CalDav Bibliothek (https://github.com/python-caldav/caldav), da sie sich auf die wesentlichen Funktionen wie Erstellen, Löschen etc. beschränkt und gut dokumentiert ist.  
Um eine Verbindung zu einem Kalender herstellen zu können, benötigt es eine URL, Username und Passwort für den Kalender. Weil es sich hierbei aber um sensible, persönliche Daten handelt, habe ich eine JSON Datei erstellt, in welcher diese Daten gespeichert werden. In der "init"-Methode des Skills werden diese Daten aus dem JSON gelesen und der CalDAV-Client initialisiert. Damit haben alle Methoden der Klasse einen Zugriff auf den Kalender.

### Nächsten Termin abfragen

Mit z.B. dem Intent "What's my next appointment" lässt sich der zeitlich nächste Kalendereintrag abfragen.  
Die Funktion sucht dabei alle Einträge in dem Kalender zwischen dem jetzigen Zeitpunkt und der Zukunft, weil es unbekannt ist, wann der nächste Eintrag ist. Dabei werden zusätzlich bereits stattfindende Einträge ignoriert. Die Liste an Einträgen, die man dadurch erhält, muss erneut nach Startzeitpunkt sortiert werden, weil es sonst eine Trennung zwischen Ganztägigen und normalen Einträgen gibt.  
Nach der Sortierung wird der zeitlich nähste Eintrag von Mycroft in einem Dialog ausgegeben.

### Termin erstellen

Mit z.B. dem Intent "Create a new event for me" lässt sich ein neuer Kalendereintrag erstellen.  
Die Methode überprüft als Erstes, ob in dem Intent bereits der Name des neuen Kalendereintrags und das Datum vorhanden ist. Falls nicht, werden Name und Datum über verschiedene Dialoge erfragt. Zusätzlich wird bei dem Datum überprüft, ob gleichzeitig eine Uhrzeit genannt wurde. Hier wird ansonsten extra gefragt, ob es sich um ein ganztätiges Event handeln soll, oder noch eine Uhrzeit hinzugefügt werden soll. Sobald alle Informationen vorhanden sind, wir ein neues Kalendereintrag-Objekt erstellt und in dem Kalender gespeichert.

### Termin löschen

Mit z.B. dem Intent "Delete an appointment called {name}" lässt sich ein Kalendereintrag löschen.  
Die Methode überprüft als Erstes, ob in dem Intent bereits der Name des Kalendereintrags vorhanden ist. Falls nicht, wird der Name über einen Dialog erfragt. Anschließend wird in dem Kalender nach einem Kalendereintrag mit diesem Namen gesucht. Falls ein solcher Eintrag gefunden wurde, wird eine Bestätigung des Users verlangt und der Eintrags gelöscht. Anonsten wird dem User mitgeteilt, dass kein Eintrag mit einem solchem Namen gefunden wurde.

### Termin umbenennen

Mit z.B. dem Intent "I want to rename an appointment." lässt sich ein Kalendereintrag umbenennen.  
Die Methode überprüft als Erstes, ob in dem Intent bereits der Name des Kalendereintrags und der neue Name vorhanden ist. Falls nicht, werden sie über verschiedene Dialoge erfragt. Danach muss der User den neuen Namen bestätigen und falls ein Kalendereintrag mit dem Namen bereits besteht, wird der Name in den neuen Namen geändert und gespeichert. Anonsten wird dem User mitgeteilt, dass kein Eintrag mit einem solchem Namen gefunden wurde.


### Alle Termine an einem Tag abfragen

Mit z.B. dem Intent "Tell me all event for the day." lassen sich alle Kalendereinträge für einen Tag abfragen.  
Die Methode überprüft als Erstes, ob in dem Intent bereits das Datum vorhanden ist. Falls nicht, wird es über ein Dialog erfragt. Danach werden alle Einträge aus dem Kalender an diesem Tag abgefragt und dem User mitgeteilt