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

### Allgemeine Funktionen

Für den Appointment-Skill habe ich als Erstes eine passende Bibliothek von Python gesucht, mit welcher man auf einen Kalender zugreifen kann. Meine Wahl fiel auf die CalDav Bibliothek (https://github.com/python-caldav/caldav), da sie sich auf die wesentlichen Funktionen wie Erstellen, Löschen etc. beschränkt und gut dokumentiert ist.