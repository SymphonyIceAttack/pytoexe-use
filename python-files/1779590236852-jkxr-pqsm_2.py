import tkinter as tk
from tkinter import scrolledtext
import random

# ------------------------------------------------------------
# HILFSFUNKTIONEN
# ------------------------------------------------------------
def shuffle_question(frage):
    options = frage["optionen"]
    correct_index = frage["richtig"]
    correct_text = options[correct_index]
    shuffled = options.copy()
    random.shuffle(shuffled)
    new_correct_index = shuffled.index(correct_text)
    return {
        "text": frage["text"],
        "optionen": shuffled,
        "richtig": new_correct_index
    }

def insert_formatted(text_widget, raw_text, font_family="Segoe UI", normal_size=12, bold_size=12):
    text_widget.configure(state=tk.NORMAL)
    text_widget.delete("1.0", tk.END)
    text_widget.tag_configure("bold", font=(font_family, bold_size, "bold"), spacing1=4, spacing2=2)
    text_widget.tag_configure("normal", font=(font_family, normal_size), spacing1=4, spacing2=2)
    parts = raw_text.split("**")
    for i, part in enumerate(parts):
        if i % 2 == 0:
            text_widget.insert(tk.END, part, "normal")
        else:
            text_widget.insert(tk.END, part, "bold")
    text_widget.configure(state=tk.DISABLED)

# ------------------------------------------------------------
# THEMA 1 – GRUNDLAGEN (ausführliche Erklärung + 30 Fragen)
# ------------------------------------------------------------
thema1_zusammenfassung = (
    "**Was ist ein Projekt?**\n"
    "Ein Projekt ist eine **zeitlich begrenzte**, **einmalige** Aufgabe mit einem **klaren Ziel**. "
    "Es unterscheidet sich von Routineaufgaben grundlegend. Beispiele: Neues Produkt entwickeln, Software einführen, Festival organisieren.\n\n"
    "**Die vier Phasen (nach DIN 69901 / ISO 21500):**\n"
    "1. **Initiierung**: Was wollen wir erreichen? → Projektauftrag und Business Case werden definiert.\n"
    "2. **Planung**: Wie kommen wir ans Ziel? → Arbeitspakete, Zeitplan, Kosten, Ressourcen und Risiken werden geplant.\n"
    "3. **Umsetzung & Steuerung**: Ausführen, Fortschritt prüfen und bei Abweichungen eingreifen.\n"
    "4. **Abschluss**: Ergebnis übergeben, Verträge beenden, dokumentieren und Lessons Learned sammeln.\n\n"
    "**Warum sind erfolgreiche Projekte erfolgreich?**\n"
    "Die Erfolgsfaktoren sind die Grundpfeiler:\n"
    "• **Klare Rollen & Verantwortlichkeiten**: Jeder weiß, was er zu tun hat.\n"
    "• **Starke Führung & Entscheidungsfähigkeit**: Der Projektleiter trifft klare Entscheidungen.\n"
    "• **Offene Kommunikation**: Regelmäßiger Austausch zwischen allen Beteiligten.\n"
    "• **Kontinuierliche Verbesserung**: Aus Fehlern lernen und Prozesse optimieren.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• Projekt = zeitlich begrenzt, einmalig, zielorientiert, komplex\n"
    "• Initiierung = Phase mit Projektauftrag und Business Case\n"
    "• Planung = Phase der Detailplanung (Arbeitspakete, Zeit, Kosten, Risiken)\n"
    "• Umsetzung & Steuerung = Phase der Ausführung und Überwachung\n"
    "• Abschluss = Phase der Übergabe, Dokumentation, Lessons Learned\n"
    "• KVP = Kontinuierlicher Verbesserungsprozess\n"
    "• Lessons Learned = Dokumentation von Erfahrungen für zukünftige Projekte\n"
    "• Business Case = wirtschaftliche Rechtfertigung des Projekts\n"
    "• Lenkungsausschuss = überwacht das Projekt auf oberster Ebene\n"
    "• Projektauftrag = Dokument mit Zielen, Umfang, Budget, Terminen, Rollen\n"
    "• Meilenstein = wichtiger Termin oder Ereignis im Projektverlauf\n"
    "• Scope = Leistungsumfang des Projekts\n"
    "• Scope Creep = unkontrollierte Ausweitung des Projektumfangs\n"
    "• Projektabschlussbericht = Dokumentation der Ergebnisse und Erfahrungen\n"
    "• Stakeholder = Person oder Gruppe mit Interesse am Projekt\n"
    "• Stakeholder-Analyse = Identifikation und Bewertung von Interessengruppen\n"
    "• DIN 69901 = deutsche Norm für Projektmanagement\n"
    "• Projektportfolio = Gesamtheit aller Projekte einer Organisation\n"
    "• Effektiv = das Richtige tun; effizient = etwas richtig tun\n"
    "• Kick-Off = Startmeeting zu Projektbeginn\n"
    "• Projektsteuerung = Planabweichungen früh erkennen und korrigieren\n"
    "• Auftraggeber (Sponsor) = zahlt, trifft strategische Entscheidungen\n"
    "• Projektleiter = plant, steuert, führt das Team\n"
    "• Projektteam = operative Umsetzung\n"
)

thema1_fragen = [
    {"text": "Welches Merkmal kennzeichnet ein Projekt im Unterschied zu einer Routineaufgabe?", "optionen": ["Wiederholung täglich", "Einmaligkeit und klare Zielvorgabe", "Unbegrenzte Zeit"], "richtig": 1},
    {"text": "In welcher Prozessgruppe wird der formelle Projektauftrag erteilt?", "optionen": ["Planung", "Initiierung", "Abschluss"], "richtig": 1},
    {"text": "Was ist KEIN typischer Erfolgsfaktor für Projekte?", "optionen": ["Klare Rollen", "Starre, unveränderliche Pläne", "Offene Kommunikation"], "richtig": 1},
    {"text": "Wofür steht die Abkürzung 'KVP'?", "optionen": ["Kostenplanung", "Kontinuierlicher Verbesserungsprozess", "Komplexe Vorgangsplanung"], "richtig": 1},
    {"text": "In welcher Phase findet die formelle Abnahme statt?", "optionen": ["Umsetzung", "Planung", "Abschluss"], "richtig": 2},
    {"text": "Was ist das Ziel der Initiierungsphase?", "optionen": ["Detaillierte Planung", "Definition des Projektziels und Auftragserteilung", "Übergabe des Produkts"], "richtig": 1},
    {"text": "Was bedeutet 'Lessons Learned'?", "optionen": ["Nachträgliche Budgeterhöhung", "Dokumentation von Erfahrungen für zukünftige Projekte", "Personalabbau"], "richtig": 1},
    {"text": "Welche Aussage über Projekte ist richtig?", "optionen": ["Projekte sind wiederkehrende Aufgaben", "Projekte sind immer komplex", "Projekte sind zeitlich begrenzt und einmalig"], "richtig": 2},
    {"text": "Was ist der Unterschied zwischen einem Projekt und einem Programm?", "optionen": ["Ein Projekt ist größer", "Ein Programm besteht aus mehreren zusammenhängenden Projekten", "Kein Unterschied"], "richtig": 1},
    {"text": "Wer ist für den Erfolg eines Projekts hauptverantwortlich?", "optionen": ["Das Team", "Der Projektleiter", "Der Auftraggeber"], "richtig": 1},
    {"text": "Was ist ein Business Case?", "optionen": ["Technische Spezifikation", "Wirtschaftliche Rechtfertigung des Projekts", "Terminplan"], "richtig": 1},
    {"text": "Welche Rolle spielt der Lenkungsausschuss?", "optionen": ["Operative Umsetzung", "Strategische Entscheidungen und Freigaben", "Tägliche Teamführung"], "richtig": 1},
    {"text": "Was versteht man unter 'Projektmanagement'?", "optionen": ["Nur Terminplanung", "Anwendung von Wissen, Werkzeugen und Techniken zur Projektsteuerung", "Budgetverwaltung"], "richtig": 1},
    {"text": "Welches Dokument legt Ziele, Umfang und Verantwortlichkeiten zu Beginn fest?", "optionen": ["Projektstrukturplan", "Projektauftrag", "Lastenheft"], "richtig": 1},
    {"text": "Was ist ein Meilenstein?", "optionen": ["Wichtiger Termin oder Ereignis", "Kleine Aufgabe", "Risiko"], "richtig": 0},
    {"text": "Was ist der Unterschied zwischen Aufgabe und Arbeitspaket?", "optionen": ["Kein Unterschied", "Arbeitspaket ist eine Gruppe von Aufgaben", "Aufgaben sind größer"], "richtig": 1},
    {"text": "Was bedeutet 'Scope'?", "optionen": ["Zeitplan", "Leistungsumfang des Projekts", "Budget"], "richtig": 1},
    {"text": "Was ist 'Scope Creep'?", "optionen": ["Schnelle Planung", "Unkontrollierte Ausweitung des Projektumfangs", "Budgetkürzung"], "richtig": 1},
    {"text": "Wozu dient ein Projektabschlussbericht?", "optionen": ["Fehler vertuschen", "Dokumentation der Ergebnisse und Erfahrungen", "Budget erhöhen"], "richtig": 1},
    {"text": "Typische Projektrollen?", "optionen": ["Nur Projektleiter", "Auftraggeber, Projektleiter, Team, Lenkungsausschuss", "Nur das Team"], "richtig": 1},
    {"text": "Vorteil standardisierter PM-Prozesse?", "optionen": ["Mehr Bürokratie", "Wiederholbarkeit und Effizienz", "Weniger Flexibilität"], "richtig": 1},
    {"text": "Was ist 'Projektkultur'?", "optionen": ["Büroausstattung", "Gemeinsame Werte, Normen und Verhaltensweisen im Team", "Projektsprache"], "richtig": 1},
    {"text": "Was ist eine Stakeholder-Analyse?", "optionen": ["Budgetanalyse", "Identifikation und Bewertung von Interessengruppen", "Risikoanalyse"], "richtig": 1},
    {"text": "Welche Norm beschreibt Projektmanagement?", "optionen": ["DIN 69901", "DIN 5008", "ISO 26000"], "richtig": 0},
    {"text": "Hauptaufgabe des Projektleiters?", "optionen": ["Selbst alle Arbeiten erledigen", "Planen, Steuern, Überwachen, Kommunizieren", "Nur Berichte schreiben"], "richtig": 1},
    {"text": "Was ist ein Projektportfolio?", "optionen": ["Ordner mit Dokumenten", "Gesamtheit aller Projekte einer Organisation", "Software"], "richtig": 1},
    {"text": "Effektiv vs. effizient?", "optionen": ["Kein Unterschied", "Effektiv = das Richtige tun, effizient = etwas richtig tun", "Effizient = das Richtige tun"], "richtig": 1},
    {"text": "Welche Phase folgt auf die Planung?", "optionen": ["Initiierung", "Umsetzung/Steuerung", "Abschluss"], "richtig": 1},
    {"text": "Was ist ein 'Kick-Off'?", "optionen": ["Projektabschlussfeier", "Startmeeting zu Projektbeginn", "Budgetprüfung"], "richtig": 1},
    {"text": "Ziel der Projektsteuerung?", "optionen": ["Planabweichungen früh erkennen und korrigieren", "Projekt schnell beenden", "Budget ausgeben"], "richtig": 0},
]

# ------------------------------------------------------------
# THEMA 2 – PROJEKTZIELE & ANFORDERUNGEN (ausführlich + 30 Fragen)
# ------------------------------------------------------------
thema2_zusammenfassung = (
    "**SMART‑Ziele – der Schlüssel zum Erfolg**\n"
    "Ziele sind die Landkarte eines Projekts. Die SMART-Formel hilft, sie klar und erreichbar zu machen:\n"
    "• **S**pezifisch: genau beschrieben (nicht 'besser werden' sondern 'Umsatz um 10% steigern').\n"
    "• **M**essbar: mit Zahlen oder klaren Kriterien prüfbar.\n"
    "• **A**ttraktiv / akzeptiert: alle Beteiligten sehen einen Nutzen und tragen das Ziel mit.\n"
    "• **R**ealistisch: mit vorhandenem Budget und Zeit erreichbar.\n"
    "• **T**erminiert: mit festem Enddatum.\n\n"
    "**Anforderungen aus Kundensicht erfassen**\n"
    "Die Basis jedes guten Ergebnisses. Man fragt sich:\n"
    "• **Wer?**: Stakeholder identifizieren (Kunde, Nutzer, Management, Lieferanten).\n"
    "• **Wie?**: Methoden wie Interviews, Workshops, Fragebögen einsetzen.\n"
    "• **Was genau?**: Kategorien: funktionale (Was soll das System tun?) und nicht‑funktionale (Sicherheit, Geschwindigkeit) Anforderungen.\n"
    "• **Wichtig?**: Priorisierung mit Methoden wie **MoSCoW** – **M**uss, **S**oll, **K**ann, **W**unsch.\n\n"
    "**Lastenheft vs. Pflichtenheft – die Zwei-Dokumente-Strategie**\n"
    "Diese beiden Dokumente schaffen Klarheit zwischen Auftraggeber und -nehmer:\n"
    "• **Lastenheft** (Auftraggeber): Das 'Was'. Hier werden die Wünsche, Ziele und Rahmenbedingungen beschrieben.\n"
    "• **Pflichtenheft** (Auftragnehmer): Das 'Wie'. Eine konkrete Antwort auf das Lastenheft mit Technik, Architektur und Testspezifikationen.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• SMART = spezifisch, messbar, attraktiv, realistisch, terminiert\n"
    "• MoSCoW = Must (Muss), Should (Soll), Could (Kann), Won‘t (Wunsch)\n"
    "• Lastenheft = Was der Kunde will (Auftraggebersicht)\n"
    "• Pflichtenheft = Wie umgesetzt wird (Auftragnehmersicht)\n"
    "• Funktionale Anforderungen = was das System tun soll\n"
    "• Nicht‑funktionale Anforderungen = Qualität, Performance, Sicherheit, Verfügbarkeit\n"
    "• Stakeholder = Kunde, Nutzer, Management, Lieferanten\n"
    "• User Story = 'Als … möchte ich … um …'\n"
    "• Akzeptanzkriterium = Bedingung für Fertigstellung einer Anforderung\n"
    "• Verifikation = Prüfung, ob Spezifikation erfüllt wird\n"
    "• Validierung = Prüfung, ob Kundenbedürfnisse erfüllt werden\n"
    "• Proof of Concept = Machbarkeitsnachweis\n"
    "• Change Request = formeller Änderungsantrag an Anforderungen\n"
    "• Traceability Matrix = Verbindung zwischen Anforderungen und Tests\n"
    "• MVP (Minimum Viable Product) = minimales Produkt für erstes Feedback\n"
    "• Prototyp = frühe Visualisierung zur Anforderungsklärung\n"
    "• Elicitation = Erhebung von Anforderungen (Interviews, Workshops)\n"
)

thema2_fragen = [
    {"text": "Wofür steht das 'M' in SMART?", "optionen": ["Messbar", "Mächtig", "Mitarbeiterorientiert"], "richtig": 0},
    {"text": "Welches Dokument beschreibt die Umsetzung aus Auftragnehmersicht?", "optionen": ["Lastenheft", "Pflichtenheft", "Projektstrukturplan"], "richtig": 1},
    {"text": "Mit welcher Methode priorisiert man (Muss, Soll, Kann, Wunsch)?", "optionen": ["SMART", "MoSCoW", "SWOT"], "richtig": 1},
    {"text": "Was bedeutet das 'A' in SMART?", "optionen": ["Absolut sicher", "Attraktiv / akzeptiert", "Ausführlich"], "richtig": 1},
    {"text": "Primäre Aufgabe des Lastenhefts?", "optionen": ["Technische Spezifikation", "Definition der Anforderungen aus Auftraggebersicht", "Budgetfestlegung"], "richtig": 1},
    {"text": "Welche gehört zu einer nicht-funktionalen Anforderung?", "optionen": ["Anmeldung mit E-Mail", "Verfügbarkeit 99,9%", "Wöchentlicher Bericht"], "richtig": 1},
    {"text": "Was sind funktionale Anforderungen?", "optionen": ["Was das System tun soll", "Sicherheitsaspekte", "Leistungsmerkmale"], "richtig": 0},
    {"text": "Wer sind typische Stakeholder?", "optionen": ["Nur der Kunde", "Kunde, Nutzer, Management, Lieferanten", "Nur der Projektleiter"], "richtig": 1},
    {"text": "Welche Technik eignet sich zur Anforderungserhebung?", "optionen": ["Gantt-Diagramm", "Interviews und Workshops", "Netzplan"], "richtig": 1},
    {"text": "Was ist eine User Story?", "optionen": ["Technisches Dokument", "Kurze Anforderung aus Anwendersicht", "Budgetplan"], "richtig": 1},
    {"text": "Was bedeutet 'Priorisierung' von Anforderungen?", "optionen": ["Zufällige Reihenfolge", "Festlegung der Wichtigkeit und Reihenfolge der Umsetzung", "Löschen unwichtiger Anforderungen"], "richtig": 1},
    {"text": "Welche Rolle spielt der Product Owner bei Anforderungen?", "optionen": ["Technische Umsetzung", "Priorisierung und Verwaltung des Backlogs", "Teamführung"], "richtig": 1},
    {"text": "Was ist ein 'Soll-Zustand'?", "optionen": ["Aktueller Zustand", "Angestrebter Zustand nach Projektabschluss", "Budget"], "richtig": 1},
    {"text": "Was beschreibt ein 'Use Case'?", "optionen": ["Kostenaufstellung", "Typischer Ablauf einer Anwendung aus Nutzersicht", "Risikoanalyse"], "richtig": 1},
    {"text": "Was ist ein 'Business Requirement'?", "optionen": ["Technische Anforderung", "Geschäftliches Ziel oder Erfordernis", "Designvorgabe"], "richtig": 1},
    {"text": "Was ist eine 'Anforderungsanalyse'?", "optionen": ["Budgetprüfung", "Systematische Erfassung und Bewertung von Anforderungen", "Teammeeting"], "richtig": 1},
    {"text": "Welche Dokumentation ist bei agilen Projekten üblich?", "optionen": ["Umfangreiche Pflichtenhefte", "User Stories und Akzeptanzkriterien", "Keine Dokumentation"], "richtig": 1},
    {"text": "Was ist ein 'Akzeptanzkriterium'?", "optionen": ["Vertragsbedingung", "Bedingung, die erfüllt sein muss, damit eine Anforderung als erledigt gilt", "Budgetgrenze"], "richtig": 1},
    {"text": "Was bedeutet 'Verifikation'?", "optionen": ["Überprüfung, ob das Produkt die Spezifikation erfüllt", "Überprüfung, ob das Produkt die Kundenbedürfnisse erfüllt", "Abnahme"], "richtig": 0},
    {"text": "Was bedeutet 'Validierung'?", "optionen": ["Überprüfung der Spezifikation", "Überprüfung, ob das Produkt die Kundenbedürfnisse erfüllt", "Testen"], "richtig": 1},
    {"text": "Was ist ein 'Proof of Concept'?", "optionen": ["Machbarkeitsnachweis", "Projektplan", "Budgetantrag"], "richtig": 0},
    {"text": "Welche Rolle spielt der Kunde bei der Anforderungsanalyse?", "optionen": ["Keine", "Liefert Anforderungen und priorisiert", "Schreibt den Code"], "richtig": 1},
    {"text": "Was ist ein 'Change Request'?", "optionen": ["Fehlerbericht", "Formeller Änderungsantrag an Anforderungen", "Projektabschluss"], "richtig": 1},
    {"text": "Was ist eine 'Traceability Matrix'?", "optionen": ["Budgettabelle", "Verbindung zwischen Anforderungen und Tests/Ergebnissen", "Zeitplan"], "richtig": 1},
    {"text": "Was ist ein 'MVP' (Minimum Viable Product)?", "optionen": ["Maximales Produkt", "Produkt mit minimalen Funktionen für erstes Kundenfeedback", "Marketingdokument"], "richtig": 1},
    {"text": "Was ist eine 'Anforderungslücke'?", "optionen": ["Fehlende Budgetposition", "Nicht erfasste Anforderung", "Zu viele Anforderungen"], "richtig": 1},
    {"text": "Was ist ein 'Stakeholder Register'?", "optionen": ["Liste aller Interessengruppen mit Eigenschaften", "Projektplan", "Risikoliste"], "richtig": 0},
    {"text": "Was bedeutet 'Elicitation'?", "optionen": ["Planung", "Erhebung von Anforderungen", "Testen"], "richtig": 1},
    {"text": "Wozu dient ein 'Prototyp'?", "optionen": ["Endprodukt", "Frühe Visualisierung zur Anforderungsklärung", "Budgetplan"], "richtig": 1},
    {"text": "Was ist eine 'nicht-funktionale Anforderung' für Sicherheit?", "optionen": ["Passwortlänge", "Login-Funktion", "Benutzerverwaltung"], "richtig": 0},
]

# ------------------------------------------------------------
# THEMA 3 – PROJEKTSTART & ORGANISATION (30 Fragen)
# ------------------------------------------------------------
thema3_zusammenfassung = (
    "**Das KickOff‑Meeting – der Startschuss für das Team**\n"
    "Ein verbindlicher Start, bei dem alle Beteiligten das erste Mal zusammenkommen. Laut DIN 69901-5 findet es nach der Planung und vor der Durchführung statt. Ziele sind:\n"
    "• Alle auf das gleiche Ziel einschwören und motivieren.\n"
    "• Projektziele, Nutzen, Rollen und Berichtswege klären.\n"
    "• Meilensteine und Kommunikationsregeln festlegen.\n\n"
    "**Das Besprechungsprotokoll – die Gedächtnisstütze des Projekts**\n"
    "Ein kurzes, verbindliches Dokument, das **Entscheidungen** (nicht die gesamte Diskussion) und **offene Punkte** festhält. Pflichtangaben sind:\n"
    "• Datum, Ort, Teilnehmer\n"
    "• Gefasste Beschlüsse\n"
    "• Maßnahmen mit Verantwortlichen und Terminen\n\n"
    "**Wichtige Rollen – das Who is Who im Projekt**\n"
    "• **Auftraggeber** (Sponsor): zahlt die Rechnung und trifft strategische Entscheidungen.\n"
    "• **Lenkungsausschuss**: überwacht das Projekt auf oberster Ebene.\n"
    "• **Projektleiter**: der 'Chef' vor Ort, plant, steuert und führt das Team.\n"
    "• **Projektteam**: die 'Macher', die operativ die Arbeit umsetzen.\n\n"
    "**Die RACI‑Matrix – wer macht eigentlich was?**\n"
    "Eine Tabelle, die Aufgaben den Rollen zuweist und so für klare Verhältnisse sorgt. Das Geheimnis ist das Prinzip der 'eindeutigen Endverantwortung': Pro Aufgabe gibt es genau ein 'A' und mindestens ein 'R'.\n"
    "• **R**esponsible = die Person(en), die die Arbeit machen.\n"
    "• **A**ccountable = die eine Person, die den Hut aufhat und die Endverantwortung trägt.\n"
    "• **C**onsulted = Spezialisten, die vorher um Rat gefragt werden müssen.\n"
    "• **I**nformed = Personen, die nachher über das Ergebnis informiert werden.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• KickOff = Startmeeting nach Planung, vor Durchführung\n"
    "• Besprechungsprotokoll = Dokument mit Entscheidungen, Verantwortlichkeiten, offenen Punkten\n"
    "• Auftraggeber (Sponsor) = Budget, Ressourcen, strategische Entscheidungen\n"
    "• Lenkungsausschuss = Überwachung auf Managementebene\n"
    "• Projektleiter = plant, steuert, führt Team\n"
    "• Projektteam = operative Umsetzung\n"
    "• RACI = Responsible (ausführend), Accountable (endverantwortlich, genau einer), Consulted (konsultiert), Informed (informiert)\n"
    "• Prinzip der eindeutigen Endverantwortung = pro Aufgabe genau ein A\n"
    "• Eskalation = Problem an höhere Ebene melden\n"
    "• Project Charter = Projektauftrag\n"
    "• Matrixorganisation = Mitarbeiter berichten an zwei Vorgesetzte (Fach- und Linie)\n"
    "• Change Control Board = Gremium für Änderungsanträge\n"
    "• Statusbericht = regelmäßiger Bericht über Fortschritt, Risiken, nächste Schritte\n"
    "• Business Analyst = analysiert und dokumentiert Anforderungen\n"
)

thema3_fragen = [
    {"text": "Hauptziel eines KickOff‑Meetings?", "optionen": ["Budget verhandeln", "Gemeinsames Verständnis schaffen", "Projekt beenden"], "richtig": 1},
    {"text": "In RACI: Welche Rolle muss genau einmal pro Aufgabe vorkommen?", "optionen": ["R", "A", "I"], "richtig": 1},
    {"text": "Was muss ein Besprechungsprotokoll enthalten?", "optionen": ["Wortprotokoll", "Entscheidungen und Verantwortlichkeiten", "Private Meinungen"], "richtig": 1},
    {"text": "Wann findet ein KickOff typischerweise statt?", "optionen": ["Vor der Planung", "Nach der Planung, vor der Durchführung", "Nach der Durchführung"], "richtig": 1},
    {"text": "Wer ist für operative Umsetzung verantwortlich?", "optionen": ["Lenkungsausschuss", "Projektleiter", "Projektteam"], "richtig": 2},
    {"text": "Prinzip der 'eindeutigen Endverantwortung' in RACI?", "optionen": ["Mehrere 'A'", "Genau ein 'A'", "Nur 'R'"], "richtig": 1},
    {"text": "Was macht der Lenkungsausschuss?", "optionen": ["Operative Arbeit", "Strategische Überwachung und Entscheidungen", "Budgetplanung"], "richtig": 1},
    {"text": "Welche Rolle stellt Budget und Ressourcen bereit?", "optionen": ["Projektteam", "Projektleiter", "Auftraggeber (Sponsor)"], "richtig": 2},
    {"text": "Was ist die Aufgabe des Projektleiters in der Organisationsphase?", "optionen": ["Team motivieren", "Rollen und Verantwortlichkeiten klären", "Programmieren"], "richtig": 1},
    {"text": "Was ist ein 'Project Charter'?", "optionen": ["Projektauftrag", "Budgetplan", "Risikoliste"], "richtig": 0},
    {"text": "Welche Kommunikationsregeln sollten im KickOff festgelegt werden?", "optionen": ["Meeting-Rhythmus, Berichtswege, Eskalation", "Private Handynummern", "Lieblingsfarbe"], "richtig": 0},
    {"text": "Was bedeutet 'Eskalation' im Projekt?", "optionen": ["Probleme an höhere Entscheidungsebene melden", "Budgeterhöhung", "Zeitplanverkürzung"], "richtig": 0},
    {"text": "Welches Tool hilft, Verantwortlichkeiten für Aufgaben darzustellen?", "optionen": ["Gantt-Diagramm", "RACI-Matrix", "Netzplan"], "richtig": 1},
    {"text": "Was ist ein 'Stakeholder'?", "optionen": ["Nur der Kunde", "Person oder Gruppe mit Interesse am Projekt", "Nur der Projektleiter"], "richtig": 1},
    {"text": "Was ist ein 'Projektorganigramm'?", "optionen": ["Darstellung der Projektorganisation und Berichtslinien", "Zeitplan", "Budgettabelle"], "richtig": 0},
    {"text": "Welche Rolle hat der 'Qualitätsmanager' im Projekt?", "optionen": ["Qualitätsziele überwachen", "Budget verwalten", "Team führen"], "richtig": 0},
    {"text": "Was ist ein 'PMO' (Project Management Office)?", "optionen": ["Projektbüro, unterstützt Projektleiter", "Externer Prüfer", "Software"], "richtig": 0},
    {"text": "Was ist ein 'Work Package Owner'?", "optionen": ["Verantwortlicher für ein Arbeitspaket", "Projektleiter", "Auftraggeber"], "richtig": 0},
    {"text": "Was sollte im Projektauftrag stehen?", "optionen": ["Ziele, Umfang, Budget, Termine, Rollen", "Nur der Projektname", "Tägliche To-dos"], "richtig": 0},
    {"text": "Was ist der Unterschied zwischen funktionaler und disziplinarischer Führung?", "optionen": ["Kein Unterschied", "Fachlich vs. Personalverantwortung", "Disziplinarisch ist wichtiger"], "richtig": 1},
    {"text": "Was ist eine 'Matrixorganisation'?", "optionen": ["Mitarbeiter berichten an zwei Vorgesetzte (Fach- und Linie)", "Reine Projektorganisation", "Stabsorganisation"], "richtig": 0},
    {"text": "Was ist ein 'Change Control Board'?", "optionen": ["Gremium zur Entscheidung über Änderungsanträge", "Team für Fehlerbehebung", "Budgetausschuss"], "richtig": 0},
    {"text": "Was ist ein 'Projekt-Tagebuch'?", "optionen": ["Persönliches Notizbuch", "Laufende Dokumentation wichtiger Ereignisse und Entscheidungen", "Finanzbuchhaltung"], "richtig": 1},
    {"text": "Was ist eine 'Projektlandkarte'?", "optionen": ["Geografische Karte", "Übersicht über alle Projekte und Abhängigkeiten", "Teamfoto"], "richtig": 1},
    {"text": "Was bedeutet 'Projektkultur' für den Start?", "optionen": ["Offene Kommunikation und Vertrauen fördern", "Strenge Hierarchien", "Keine Regeln"], "richtig": 0},
    {"text": "Welches Meeting findet einmal wöchentlich statt?", "optionen": ["Daily Scrum", "Teammeeting (Jour Fixe)", "KickOff"], "richtig": 1},
    {"text": "Was ist ein 'Statusbericht'?", "optionen": ["Regelmäßiger Bericht über Fortschritt, Risiken, nächste Schritte", "Abschlussdokument", "Budgetplan"], "richtig": 0},
    {"text": "Welche Rolle hat der 'Business Analyst'?", "optionen": ["Anforderungen analysieren und dokumentieren", "Programmieren", "Budgetplanung"], "richtig": 0},
    {"text": "Was ist ein 'Projekt-Steckbrief'?", "optionen": ["Kurzzusammenfassung des Projekts für schnelle Übersicht", "Detaillierter Plan", "Vertrag"], "richtig": 0},
    {"text": "Was ist das Ziel eines 'Team-KickOff'?", "optionen": ["Teambildung und gemeinsame Zielklärung", "Budgetverhandlung", "Vertragsunterzeichnung"], "richtig": 0},
]

# ------------------------------------------------------------
# THEMA 4 – TEAMARBEIT & KOMMUNIKATION (30 Fragen)
# ------------------------------------------------------------
thema4_zusammenfassung = (
    "**Tuckman‑Phasen – wie Teams zusammenwachsen**\n"
    "Bruce Tuckman beschrieb, dass jedes Team eine bestimmte Entwicklung durchläuft. Dies zu kennen, hilft Konflikte einzuordnen:\n"
    "1. **Forming**: Kennenlernen, höflich, zurückhaltend, noch unsicher.\n"
    "2. **Storming**: Konflikte, Machtkämpfe, Meinungsverschiedenheiten (eine gesunde und wichtige Phase!).\n"
    "3. **Norming**: Regeln und Rollen werden akzeptiert, Zusammenhalt und Vertrauen wachsen.\n"
    "4. **Performing**: Das Team ist produktiv, selbstorganisiert und liefert Höchstleistungen.\n"
    "5. **Adjourning**: Das Projekt endet, das Team löst sich auf, Erfolge werden gefeiert.\n\n"
    "**Das Vier‑Seiten‑Modell (Schulz von Thun) – die geheimen Botschaften**\n"
    "Jede Nachricht hat vier Botschaften gleichzeitig. Missverständnisse entstehen, weil der Empfänger auf eine andere 'Ohren' hört als der Sender spricht:\n"
    "• **Sachinhalt**: 'Die Ampel ist grün.' (reine Information)\n"
    "• **Selbstoffenbarung**: 'Ich achte auf die Ampel.' (Was ich über mich preisgebe)\n"
    "• **Beziehung**: 'Ich traue dir nicht, selbst zu schauen.' (Wie ich zu dir stehe)\n"
    "• **Appell**: 'Fahr jetzt los!' (Was ich bei dir erreichen will)\n\n"
    "**Aktives Zuhören – mehr als nur nicht zu unterbrechen**\n"
    "Eine Technik, um sicherzustellen, dass man den anderen wirklich versteht. Die Kernprinzipien:\n"
    "• Blickkontakt und aufmerksame Körperhaltung.\n"
    "• **Paraphrasieren**: Mit eigenen Worten wiederholen („Du meinst also…“).\n"
    "• Nachfragen, um sicherzugehen („Habe ich das richtig verstanden, dass…?“).\n"
    "• Gefühle benennen („Das scheint dich wirklich zu ärgern.“).\n"
    "• Zusammenfassen des Gesagten.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• Tuckman‑Phasen = Forming (Kennenlernen), Storming (Konflikte), Norming (Regeln), Performing (Produktivität), Adjourning (Auflösung)\n"
    "• Vier‑Seiten‑Modell = Sachinhalt, Selbstoffenbarung, Beziehung, Appell\n"
    "• Aktives Zuhören = paraphrasieren, nachfragen, Gefühle spiegeln, zusammenfassen\n"
    "• Psychologische Sicherheit = Klima, in dem Fehler zugegeben und Risiken eingegangen werden\n"
    "• Teamvertrag = gemeinsam festgelegte Regeln für Zusammenarbeit\n"
    "• Feedback = Rückmeldung geben und empfangen zur Verbesserung\n"
    "• Retrospektive = regelmäßige Reflexion der Zusammenarbeit\n"
    "• Ich‑Botschaft = konstruktive Äußerung eigener Gefühle ohne Vorwurf\n"
    "• Kommunikationsplan = wer informiert wen womit wie oft\n"
)

thema4_fragen = [
    {"text": "In welcher Tuckman-Phase treten die meisten Konflikte auf?", "optionen": ["Forming", "Storming", "Performing"], "richtig": 1},
    {"text": "Das Vier-Seiten-Modell hilft zu verstehen ...", "optionen": ["warum Missverständnisse entstehen", "wie man schneller spricht", "wie man Diagramme zeichnet"], "richtig": 0},
    {"text": "Kernprinzip des aktiven Zuhörens?", "optionen": ["Schnell eigene Lösungen", "Paraphrasieren", "Lauter sprechen"], "richtig": 1},
    {"text": "Herausforderung in der 'Storming'-Phase?", "optionen": ["Höflichkeit", "Konflikte und Machtkämpfe", "Produktivität"], "richtig": 1},
    {"text": "Appell des Satzes 'Dein Bericht ist pünktlich'?", "optionen": ["Sachinfo", "Selbstoffenbarung", "'Mach so weiter!'"], "richtig": 2},
    {"text": "Technik des aktiven Zuhörens?", "optionen": ["Kritik äußern", "Gefühle spiegeln", "Sofort Lösung anbieten"], "richtig": 1},
    {"text": "Welche Phase folgt nach 'Norming'?", "optionen": ["Storming", "Performing", "Adjourning"], "richtig": 1},
    {"text": "Was ist die Selbstoffenbarung im Vier-Seiten-Modell?", "optionen": ["Die reine Information", "Was ich über mich preisgebe", "Aufforderung zu handeln"], "richtig": 1},
    {"text": "Was fördert psychologische Sicherheit im Team?", "optionen": ["Fehler zugeben können", "Strenge Kontrolle", "Einzelkämpfertum"], "richtig": 0},
    {"text": "Was ist ein 'Teamvertrag'?", "optionen": ["Arbeitsvertrag", "Gemeinsam festgelegte Regeln für Zusammenarbeit", "Budgetplan"], "richtig": 1},
    {"text": "Welche Kommunikationsform ist bei Konflikten am besten?", "optionen": ["E-Mail", "Persönliches Gespräch", "Chat"], "richtig": 1},
    {"text": "Was bedeutet 'Feedback' im Team?", "optionen": ["Kritik üben", "Rückmeldung geben und empfangen zur Verbesserung", "Lob aussprechen"], "richtig": 1},
    {"text": "Was ist ein 'Retrospektive'?", "optionen": ["Projektabschluss", "Regelmäßige Reflexion der Zusammenarbeit", "Planungsmeeting"], "richtig": 1},
    {"text": "Welche Tuckman-Phase ist durch hohe Produktivität gekennzeichnet?", "optionen": ["Forming", "Norming", "Performing"], "richtig": 2},
    {"text": "Was ist die 'Beziehungsebene' einer Nachricht?", "optionen": ["Was ich über den Empfänger denke", "Reine Information", "Aufforderung"], "richtig": 0},
    {"text": "Was ist eine 'Ich-Botschaft'?", "optionen": ["Egoistische Aussage", "Konstruktive Äußerung eigener Gefühle, ohne Vorwurf", "Frage"], "richtig": 1},
    {"text": "Wie baut man Vertrauen im Team auf?", "optionen": ["Zuverlässigkeit, Offenheit, Respekt", "Strenge Regeln", "Wettbewerb"], "richtig": 0},
    {"text": "Was ist ein 'Meeting-Minutes'?", "optionen": ["Protokoll", "Einladung", "Tagesordnung"], "richtig": 0},
    {"text": "Was ist ein 'Konfliktlösungsmodell'?", "optionen": ["Harvard-Konzept", "Wasserfall", "Scrum"], "richtig": 0},
    {"text": "Was ist 'Nonverbale Kommunikation'?", "optionen": ["Körpersprache, Tonfall, Gestik", "Geschriebene Worte", "Zahlen"], "richtig": 0},
    {"text": "Was ist aktives Zuhören?", "optionen": ["Nicken", "Verstehen und Rückmeldung geben", "Unterbrechen"], "richtig": 1},
    {"text": "Was ist ein 'Feedback-Regelkreis'?", "optionen": ["Geben, Empfangen, Umsetzen", "Kritisieren", "Ignorieren"], "richtig": 0},
    {"text": "Welche Phase im Tuckman-Modell folgt auf 'Performing'?", "optionen": ["Storming", "Adjourning", "Norming"], "richtig": 1},
    {"text": "Was bedeutet 'Transparenz' in der Kommunikation?", "optionen": ["Alle relevanten Informationen teilen", "Geheimnisse bewahren", "Nur positives sagen"], "richtig": 0},
    {"text": "Was ist ein 'Daily Stand-up'?", "optionen": ["Tägliches kurzes Teammeeting", "Wöchentlicher Bericht", "Monatliche Retrospektive"], "richtig": 0},
    {"text": "Was ist der 'Sachinhalt' einer Nachricht?", "optionen": ["Fakten und Daten", "Gefühle", "Beziehung"], "richtig": 0},
    {"text": "Was fördert eine gute Teamkultur?", "optionen": ["Wertschätzung, Respekt, Unterstützung", "Konkurrenzkampf", "Schweigen"], "richtig": 0},
    {"text": "Was ist ein 'Teamentwicklungsmodell'?", "optionen": ["Tuckman-Phasen", "SMART", "SWOT"], "richtig": 0},
    {"text": "Was ist ein 'Kommunikationsplan'?", "optionen": ["Wer informiert wen womit wie oft?", "Projektplan", "Organigramm"], "richtig": 0},
    {"text": "Was ist die größte Herausforderung in virtuellen Teams?", "optionen": ["Technische Probleme", "Kommunikation und sozialer Austausch", "Budget"], "richtig": 1},
]

# ------------------------------------------------------------
# THEMA 5 – ANALYSE- & PLANUNGSWERKZEUGE (mit rechteckiger Netzplan-Grafik + 30 Fragen)
# ------------------------------------------------------------
thema5_zusammenfassung = (
    "**Die SWOT‑Analyse – Stärken, Schwächen, Chancen, Risiken**\n"
    "Eine Momentaufnahme, um die Ausgangslage zu verstehen.\n"
    "• **Stärken** (intern): Das, was wir gut können.\n"
    "• **Schwächen** (intern): Das, was wir weniger gut können.\n"
    "• **Chancen** (extern): Was uns von außen begünstigen könnte.\n"
    "• **Risiken** (extern): Was uns von außen bedrohen könnte.\n\n"
    "**Die Nutzwertanalyse – Entscheidungen auf Zahlen basieren**\n"
    "Eine systematische Entscheidungstechnik, wenn Sie zwischen mehreren Alternativen wählen müssen. Schritt für Schritt:\n"
    "1. **Ziele/Kriterien festlegen**: Was ist uns wichtig (z.B. Preis, Leistung)?\n"
    "2. **Kriterien gewichten**: Wie wichtig ist jedes Kriterium (z.B. in %)?\n"
    "3. **Alternativen bewerten**: Wie gut erfüllt jede Alternative jedes Kriterium (z.B. Schulnote 1-6)?\n"
    "4. **Nutzwert berechnen**: Gewichtung × Bewertung für jedes Kriterium und dann summiert.\n\n"
    "**Netzplan – Der Fahrplan Ihres Projekts**\n"
    "Ein Netzplan stellt alle Aufgaben (Vorgänge) eines Projekts sowie deren **logische und zeitliche Abhängigkeiten** grafisch dar. Er ist die Grundlage für die **Terminplanung** und hilft, **Pufferzeiten** sowie den **kritischen Pfad** zu ermitteln.\n\n"
    "**Die Berechnung des Netzplans – Schritt für Schritt**\n"
    "Jeder Vorgang wird in einem **Vorgangsknoten** zusammengefasst. Ein typischer Knoten enthält folgende Werte (rechteckige Darstellung):\n\n"
    "+-------------------+\n"
    "| Index  |    |  Dauer  |\n"
    "+-------------------+\n"
    "|     Bezeichnung      |\n"
    "+-------------------+\n"
    "| FAZ   |   GP  |  FEZ  |\n"
    "+-------------------+\n"
    "| SAZ  |    FP   | SEZ  |\n"
    "+-------------------+\n\n"
    "**Bedeutung der Abkürzungen:**\n"
    "• **FAZ** = Frühester Anfangszeitpunkt (frühestmöglicher Start)\n"
    "• **FEZ** = Frühester Endzeitpunkt (FAZ + Dauer)\n"
    "• **SAZ** = Spätester Anfangszeitpunkt (spätestmöglicher Start, ohne Projektende zu gefährden)\n"
    "• **SEZ** = Spätester Endzeitpunkt (SAZ + Dauer)\n"
    "• **GP** = Gesamtpuffer (SAZ – FAZ) – Zeitreserve, die das Projektende nicht gefährdet\n"
    "• **FP** = Freier Puffer (FAZ des Nachfolgers – FEZ) – Zeitreserve ohne Beeinflussung des Nachfolgers\n\n"
    "**So wird gerechnet:**\n"
    "1. **Vorwärtsrechnung** (FAZ → FEZ): Startvorgänge FAZ=0, FEZ=FAZ+Dauer, FAZ eines Nachfolgers = max(FEZ aller Vorgänger).\n"
    "2. **Rückwärtsrechnung** (SEZ → SAZ): Letzte Vorgänge SEZ = max(FEZ), SAZ = SEZ – Dauer, SEZ eines Vorgängers = min(SAZ aller Nachfolger).\n"
    "3. **Puffer berechnen**: GP = SAZ – FAZ, FP = min(FAZ der Nachfolger) – FEZ.\n"
    "**Kritischer Pfad** = Kette von Vorgängen mit GP = 0. Jede Verzögerung verlängert das Projekt.\n\n"
    "**Netzplan vs. Gantt‑Diagramm**\n"
    "Der **Netzplan** analysiert **Abhängigkeiten** und den **kritischen Pfad** – er ist das Werkzeug für die **Planung**.\n"
    "Das **Gantt‑Diagramm** visualisiert die Aufgaben als **Balken auf einer Zeitachse** – es ist das Werkzeug für die **Kommunikation und Fortschrittskontrolle**.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• SWOT = Strengths, Weaknesses, Opportunities, Threats\n"
    "• Nutzwertanalyse = Entscheidung mit gewichteten Kriterien\n"
    "• Netzplan = zeigt Abhängigkeiten der Vorgänge\n"
    "• FAZ = frühester Anfangszeitpunkt\n"
    "• FEZ = frühester Endzeitpunkt (FAZ + Dauer)\n"
    "• SAZ = spätester Anfangszeitpunkt\n"
    "• SEZ = spätester Endzeitpunkt (SAZ + Dauer)\n"
    "• GP (Gesamtpuffer) = SAZ – FAZ\n"
    "• FP (freier Puffer) = FAZ(Nachfolger) – FEZ\n"
    "• Kritischer Pfad = Kette mit GP = 0\n"
    "• Vorwärtsrechnung = FAZ → FEZ\n"
    "• Rückwärtsrechnung = SEZ → SAZ\n"
    "• Gantt‑Diagramm = Balken auf Zeitachse\n"
    "• PSP (Projektstrukturplan) = hierarchische Zerlegung in Arbeitspakete\n"
    "• Meilensteintrendanalyse = visuelle Darstellung von Terminabweichungen\n"
    "• PERT = Dreipunktschätzung (optimistisch, pessimistisch, wahrscheinlich)\n"
    "• Kapazitätsplan = Verfügbarkeit von Ressourcen über Zeit\n"
    "• WBS = englisch für PSP\n"
)

thema5_fragen = [
    {"text": "Wofür steht das 'O' in SWOT?", "optionen": ["Optimierung", "Opportunities (Chancen)", "Ordnung"], "richtig": 1},
    {"text": "Welche Methode findet den kritischen Pfad?", "optionen": ["Gantt", "Netzplan", "RACI"], "richtig": 1},
    {"text": "Verzögerung auf kritischem Pfad?", "optionen": ["Projektende verschiebt sich", "Andere werden schneller", "Puffer fängt ab"], "richtig": 0},
    {"text": "Erster Schritt einer Nutzwertanalyse?", "optionen": ["Alternativen auswählen", "Kriterien festlegen & gewichten", "Nutzwert berechnen"], "richtig": 1},
    {"text": "Interner Faktor in SWOT?", "optionen": ["Gesetzesänderung", "Starke eigene Marke", "Neuer Markt"], "richtig": 1},
    {"text": "Primärer Zweck eines PSP?", "optionen": ["Abhängigkeiten darstellen", "Hierarchische Zerlegung in Arbeitspakete", "Zeitachse visualisieren"], "richtig": 1},
    {"text": "Was zeigt ein Gantt-Diagramm an?", "optionen": ["Abhängigkeiten", "Dauer und zeitliche Lage von Aufgaben als Balken", "Verantwortlichkeiten"], "richtig": 1},
    {"text": "Was ist der kritische Pfad?", "optionen": ["Der teuerste Vorgang", "Längste Kette abhängiger Aufgaben ohne Puffer", "Wichtigste Meilensteine"], "richtig": 1},
    {"text": "Wofür steht 'W' in SWOT?", "optionen": ["Widerstand", "Weaknesses (Schwächen)", "Wirtschaft"], "richtig": 1},
    {"text": "Was ist ein 'Puffer' im Netzplan?", "optionen": ["Zeitreserve", "Budgetreserve", "Qualitätspuffer"], "richtig": 0},
    {"text": "Was ist eine 'Meilensteintrendanalyse'?", "optionen": ["Visuelle Darstellung von Terminabweichungen", "Kostenanalyse", "Risikoanalyse"], "richtig": 0},
    {"text": "Was ist ein 'Arbeitspaket'?", "optionen": ["Kleinste planbare Einheit im PSP", "Große Aufgabe", "Meilenstein"], "richtig": 0},
    {"text": "Welche Darstellung eignet sich für Abhängigkeiten?", "optionen": ["Gantt", "Netzplan", "RACI"], "richtig": 1},
    {"text": "Was ist ein 'Vorgang' im Netzplan?", "optionen": ["Aktivität mit Dauer", "Ereignis", "Meilenstein"], "richtig": 0},
    {"text": "Was ist ein 'Risiko' in der SWOT?", "optionen": ["Threat (extern)", "Weakness (intern)", "Opportunity"], "richtig": 0},
    {"text": "Wofür steht die Nutzwertanalyse?", "optionen": ["Entscheidungsfindung", "Terminplanung", "Risikoanalyse"], "richtig": 0},
    {"text": "Was ist ein 'Projektstrukturplan'?", "optionen": ["Hierarchische Aufteilung des Projekts", "Zeitplan", "Organigramm"], "richtig": 0},
    {"text": "Was ist eine 'Vorgangstabelle'?", "optionen": ["Liste der Aufgaben mit Vorgängern und Dauer", "Balkendiagramm", "Verantwortlichkeitsmatrix"], "richtig": 0},
    {"text": "Was ist der 'Gesamtpuffer'?", "optionen": ["Zeit, um die ein Vorgang verschoben werden kann, ohne Projektende zu gefährden", "Freier Puffer", "Kritischer Pfad"], "richtig": 0},
    {"text": "Was ist der 'freie Puffer'?", "optionen": ["Zeit, um die ein Vorgang verschoben werden kann, ohne Nachfolger zu beeinflussen", "Gesamtpuffer", "Projektpuffer"], "richtig": 0},
    {"text": "Was ist ein 'Gantt-Diagramm'?", "optionen": ["Balkendiagramm zur Zeitplanung", "Netzplan", "Matrix"], "richtig": 0},
    {"text": "Wozu dient ein 'Projektkalender'?", "optionen": ["Festlegung von Arbeitstagen und Schichten", "Budgetplanung", "Risikoliste"], "richtig": 0},
    {"text": "Was ist ein 'Ressourcenplan'?", "optionen": ["Zuordnung von Personen, Material, Budget zu Aufgaben", "Zeitplan", "Qualitätsplan"], "richtig": 0},
    {"text": "Was ist 'Kritischer Pfad' (CPM)?", "optionen": ["Methode zur Bestimmung der minimalen Projektdauer", "Kostenplanung", "Qualitätssicherung"], "richtig": 0},
    {"text": "Was ist eine 'PERT-Analyse'?", "optionen": ["Dreipunktschätzung (optimistisch, pessimistisch, wahrscheinlich)", "SWOT", "Nutzwert"], "richtig": 0},
    {"text": "Was ist ein 'Meilenstein' im Gantt?", "optionen": ["Symbol (meist Raute) für wichtigen Termin", "Aufgabenbalken", "Abhängigkeit"], "richtig": 0},
    {"text": "Was ist eine 'Ressourcenüberlastung'?", "optionen": ["Zu viele Aufgaben für eine Ressource zur gleichen Zeit", "Unterlastung", "Budgetüberschreitung"], "richtig": 0},
    {"text": "Was ist ein 'Kapazitätsplan'?", "optionen": ["Verfügbarkeit von Ressourcen über Zeit", "Projektstruktur", "Risikomatrix"], "richtig": 0},
    {"text": "Welche Software wird klassisch für Gantt genutzt?", "optionen": ["MS Project", "Excel", "Word"], "richtig": 0},
    {"text": "Was ist ein 'Work Breakdown Structure' (WBS)?", "optionen": ["Englisch für PSP", "Zeitplan", "Budget"], "richtig": 0},
]

# ------------------------------------------------------------
# THEMA 6 – AGILES PROJEKTMANAGEMENT (SCRUM) (30 Fragen)
# ------------------------------------------------------------
thema6_zusammenfassung = (
    "**Agil vs. Wasserfall – zwei Welten**\n"
    "• **Wasserfall**: Alles wird zuerst detailliert geplant, dann umgesetzt. Sehr unflexibel, der Kunde sieht das Ergebnis erst am Schluss.\n"
    "• **Agil**: Arbeit wird in kurze Zyklen (Sprints) eingeteilt. Ständiges Feedback vom Kunden, Anpassungen sind jederzeit möglich.\n\n"
    "**Die Rollen in Scrum – klar verteilt**\n"
    "• **Product Owner**: Der Chef des Produkts. Er entscheidet, welche Funktionen zuerst entwickelt werden (priorisiert das **Product Backlog**).\n"
    "• **Scrum Master**: Der Coach des Teams. Er schützt das Team vor Störungen und hilft bei der Anwendung der Scrum-Regeln.\n"
    "• **Entwicklungsteam**: Die Macher. Ein selbstorganisiertes Team, das die Arbeit in Sprints umsetzt.\n\n"
    "**Die Scrum-Events – der Rhythmus des Projekts**\n"
    "• **Sprint**: Ein festgelegter Zeitraum (meist 2-4 Wochen), in dem ein fertiges, nutzbares Inkrement entsteht.\n"
    "• **Daily Scrum**: Ein tägliches, 15-minütiges Meeting zur Abstimmung: Was habe ich gestern gemacht? Was heute? Gibt es Hindernisse?\n"
    "• **Sprint Review**: Am Ende des Sprints wird das Ergebnis dem Product Owner und Stakeholdern gezeigt und Feedback eingeholt.\n"
    "• **Sprint Retrospektive**: Das Team reflektiert seinen eigenen Prozess: Was lief gut? Was können wir verbessern?\n\n"
    "**User Stories – Anforderungen aus Anwendersicht**\n"
    "Eine einfache, aber mächtige Methode, um Anforderungen zu beschreiben. Das Format: \n"
    "**Als** [Rolle] **möchte ich** [Ziel] **um** [Nutzen] **zu erhalten.**\n"
    "Beispiel: *Als Kunde möchte ich online sehen können, ob ein Produkt auf Lager ist, um zu entscheiden, ob ich es sofort bestellen kann.*\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• Agil = iterativ, kurze Zyklen, ständiges Feedback\n"
    "• Wasserfall = linear, starre Phasen, spätes Feedback\n"
    "• Product Owner = priorisiert Product Backlog\n"
    "• Scrum Master = schützt Team, hilft bei Scrum-Regeln\n"
    "• Entwicklungsteam = selbstorganisiert, setzt um\n"
    "• Product Backlog = priorisierte Liste aller gewünschten Funktionen\n"
    "• Sprint Backlog = Aufgaben für den aktuellen Sprint\n"
    "• Increment = fertiges, nutzbares Zwischenergebnis eines Sprints\n"
    "• Sprint = fester Zeitraum (2-4 Wochen)\n"
    "• Daily Scrum = max. 15 min, tägliche Abstimmung\n"
    "• Sprint Review = Ergebnis zeigen, Feedback holen\n"
    "• Sprint Retrospektive = Prozess verbessern\n"
    "• User Story = 'Als … möchte ich … um …'\n"
    "• Definition of Done = Kriterien für Fertigstellung einer Story\n"
    "• Planning Poker = gemeinsame Aufwandsschätzung mit Karten\n"
    "• Zeitbox = feste maximale Dauer für ein Event\n"
    "• Velocity = Story Points pro Sprint (Geschwindigkeit)\n"
    "• Burndown Chart = verbleibender Aufwand über Zeit\n"
    "• Scrum of Scrums = Abstimmungsmeeting mehrerer Scrum-Teams\n"
    "• Kanban Board = Visualisierung des Arbeitsflusses (To‑Do, In Progress, Done)\n"
    "• Story Point = Einheit für Aufwandsschätzung\n"
    "• Epic = große User Story, zerlegbar\n"
    "• Task Board = Board mit Aufgaben-Status\n"
    "• Continuous Improvement = ständige Verbesserung durch Retrospektive\n"
    "• Release Plan = Plan für mehrere Sprints bis Auslieferung\n"
    "• TDD = Test-Driven Development (Tests vor Code)\n"
    "• Pair Programming = zwei Programmierer an einem Rechner\n"
    "• Minimum Marketable Feature = kleinste auslieferbare Funktion mit Nutzen\n"
    "• Sprint Goal = Ziel des Sprints\n"
    "• Product Goal = langfristiges Produktziel\n"
)

thema6_fragen = [
    {"text": "Wer priorisiert das Product Backlog?", "optionen": ["Scrum Master", "Product Owner", "Team"], "richtig": 1},
    {"text": "Typische Sprintlänge?", "optionen": ["1 Tag", "2-4 Wochen", "3 Monate"], "richtig": 1},
    {"text": "Methode zur Aufwandsschätzung in Scrum?", "optionen": ["Planning Poker", "Wasserfall", "SWOT"], "richtig": 0},
    {"text": "Hauptziel der Sprint-Retrospektive?", "optionen": ["Produkt zeigen", "Prozess verbessern", "Nächste Sprint planen"], "richtig": 1},
    {"text": "Was ist ein Product Backlog?", "optionen": ["Fehlerliste", "Priorisierte Liste aller gewünschten Funktionen", "Daily-Protokoll"], "richtig": 1},
    {"text": "Rolle des Scrum Masters?", "optionen": ["Disziplinarischer Vorgesetzter", "Verantwortlich für Scrum-Regeln im Team", "Alleiniger Entscheider über Features"], "richtig": 1},
    {"text": "Was ist ein 'Increment' in Scrum?", "optionen": ["Planungsdokument", "Fertiges, nutzbares Zwischenergebnis eines Sprints", "Hindernisliste"], "richtig": 1},
    {"text": "Was passiert im Daily Scrum?", "optionen": ["Ausführliche Besprechung", "Max. 15-minütige Abstimmung", "Präsentation vor Kunden"], "richtig": 1},
    {"text": "Was ist ein 'Sprint Backlog'?", "optionen": ["Liste der Aufgaben für den aktuellen Sprint", "Gesamtliste aller Anforderungen", "Retrospektive"], "richtig": 0},
    {"text": "Was ist eine 'User Story'?", "optionen": ["Technische Spezifikation", "Anforderung aus Anwendersicht", "Testfall"], "richtig": 1},
    {"text": "Was ist 'Definition of Done'?", "optionen": ["Kriterien für Fertigstellung", "Projektende", "Sprintende"], "richtig": 0},
    {"text": "Was ist ein 'Sprint Review'?", "optionen": ["Ergebnis zeigen", "Teaminterne Retrospektive", "Planung"], "richtig": 0},
    {"text": "Was ist ein 'Product Owner'?", "optionen": ["Verantwortlich für Produktwert", "Prozessverantwortlicher", "Entwickler"], "richtig": 0},
    {"text": "Was ist ein 'Scrum Team'?", "optionen": ["PO, SM, Entwicklungsteam", "Nur Entwickler", "Nur PO und SM"], "richtig": 0},
    {"text": "Was bedeutet 'Zeitbox' in Scrum?", "optionen": ["Feste maximale Dauer", "Unbegrenzte Zeit", "Zeit für Pausen"], "richtig": 0},
    {"text": "Was ist ein 'Sprint Planning'?", "optionen": ["Auswahl der Stories für den Sprint", "Retrospektive", "Daily"], "richtig": 0},
    {"text": "Was ist 'Velocity'?", "optionen": ["Geschwindigkeit des Teams", "Anzahl der Fehler", "Budget"], "richtig": 0},
    {"text": "Was ist ein 'Burndown Chart'?", "optionen": ["Verbleibender Aufwand über Zeit", "Gantt", "Netzplan"], "richtig": 0},
    {"text": "Was ist 'Scrum of Scrums'?", "optionen": ["Mehrere Teams", "Erweiterte Retrospektive", "Daily für PO"], "richtig": 0},
    {"text": "Was ist ein 'Kanban Board'?", "optionen": ["Visualisierung des Arbeitsflusses", "Backlog", "Sprint-Board"], "richtig": 0},
    {"text": "Was ist ein 'Story Point'?", "optionen": ["Aufwandseinheit", "Stunden", "Priorität"], "richtig": 0},
    {"text": "Was ist ein 'Epic'?", "optionen": ["Große Story, zerlegbar", "Kleine Aufgabe", "Fehler"], "richtig": 0},
    {"text": "Was ist ein 'Task Board'?", "optionen": ["To-Do, In Progress, Done", "Backlog", "Plan"], "richtig": 0},
    {"text": "Was ist 'Continuous Improvement' in Scrum?", "optionen": ["Retrospektive", "Dokumentation", "Planung"], "richtig": 0},
    {"text": "Was ist ein 'Release Plan'?", "optionen": ["Plan für mehrere Sprints", "Sprintplan", "Backlog"], "richtig": 0},
    {"text": "Was ist 'Test-Driven Development'?", "optionen": ["Tests vor Code", "Code vor Tests", "Keine Tests"], "richtig": 0},
    {"text": "Was ist 'Pair Programming'?", "optionen": ["Zwei an einem Rechner", "Code-Review", "Alleine"], "richtig": 0},
    {"text": "Was ist ein 'Minimum Marketable Feature'?", "optionen": ["Kleinste auslieferbare Funktion", "MVP", "Epic"], "richtig": 0},
    {"text": "Was ist ein 'Sprint Goal'?", "optionen": ["Ziel des Sprints", "Aufgabenliste", "Definition of Done"], "richtig": 0},
    {"text": "Was ist ein 'Product Goal'?", "optionen": ["Langfristiges Ziel", "Sprintziel", "Release-Ziel"], "richtig": 0},
]

# ------------------------------------------------------------
# THEMA 7 – QUALITÄTSMANAGEMENT (30 Fragen)
# ------------------------------------------------------------
thema7_zusammenfassung = (
    "**Was ist Qualität? – Mehr als nur 'gut'**\n"
    "Qualität ist, wenn ein Produkt oder eine Dienstleistung die **festgelegten Anforderungen** (oder noch besser: die **Erwartungen der Kunden**) erfüllt. Es geht um das, was zählt:\n"
    "• **Funktionalität**: Tut es, was es soll?\n"
    "• **Zuverlässigkeit**: Funktioniert es auch unter Belastung?\n"
    "• **Benutzerfreundlichkeit**: Ist es einfach zu bedienen?\n"
    "• **Sicherheit**: Schützt es den Benutzer und seine Daten?\n\n"
    "**Die ISO 9000‑Familie – der internationale Rahmen**\n"
    "• **ISO 9000**: Grundlagen und Begriffe (das Nachschlagewerk).\n"
    "• **ISO 9001**: Die zentrale Norm mit den **Anforderungen** an ein QM-System. Sie ist die Grundlage für Zertifizierungen.\n"
    "• **ISO 9004**: Ein Leitfaden für nachhaltigen Erfolg, der über die Mindestanforderungen hinausgeht.\n\n"
    "**PDCA‑Zyklus – der Motor der kontinuierlichen Verbesserung**\n"
    "Ein endloser Kreislauf, um Qualität systematisch zu steigern:\n"
    "• **P**lan: Ziele festlegen, Prozesse planen, Maßnahmen zur Verbesserung identifizieren.\n"
    "• **D**o: Die geplanten Maßnahmen umsetzen.\n"
    "• **C**heck: Die Ergebnisse überwachen und prüfen, ob die Ziele erreicht wurden.\n"
    "• **A**ct: Aus den Erkenntnissen lernen, erfolgreiche Änderungen standardisieren und bei Bedarf Korrekturen vornehmen.\n\n"
    "**Weitere wichtige QM-Methoden**\n"
    "• **KVP** (Kontinuierlicher Verbesserungsprozess): Der Überbegriff für viele kleine, ständige Verbesserungen.\n"
    "• **FMEA** (Fehlermöglichkeits- und Einflussanalyse): Eine Methode, um potenzielle Fehler zu erkennen, bevor sie passieren.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• Qualität = Erfüllung von Anforderungen/Kundenerwartungen\n"
    "• ISO 9001 = zentrale Zertifizierungsnorm für QM\n"
    "• ISO 9000 = Grundlagen und Begriffe\n"
    "• ISO 9004 = Leitfaden für nachhaltigen Erfolg\n"
    "• PDCA = Plan‑Do‑Check‑Act (kontinuierliche Verbesserung)\n"
    "• FMEA = Fehlermöglichkeits- und Einflussanalyse\n"
    "• KVP = Kontinuierlicher Verbesserungsprozess\n"
    "• Audit = systematische Prüfung der Prozesseinhaltung\n"
    "• Zero Defects = Fehlerfreiheit als Ziel\n"
    "• TQM = Total Quality Management (umfassendes QM)\n"
    "• Qualitätszirkel = Mitarbeitergruppe zur Verbesserung\n"
    "• Fehlerkosten = Nacharbeit, Garantie, Vertrauensverlust\n"
    "• Prüfkosten = Tests und Audits\n"
    "• Vermeidungskosten = Schulungen, Prozessverbesserung\n"
    "• Six Sigma = Methode zur Fehlerreduzierung (DMAIC)\n"
    "• Lean Management = Verschwendung reduzieren, Wert maximieren\n"
    "• Kaizen = japanisch für kontinuierliche Verbesserung\n"
    "• Qualitätssicherung (QS) = prozessorientierte Fehlervermeidung\n"
    "• Qualitätskontrolle (QK) = produktorientierte Prüfung\n"
)

thema7_fragen = [
    {"text": "Was beschreibt der PDCA-Zyklus?", "optionen": ["Wasserfall", "Kontinuierliche Verbesserung", "Budgetplanung"], "richtig": 1},
    {"text": "Welche ISO-Norm ist zertifizierungsrelevant?", "optionen": ["ISO 9001:2015", "ISO 21500", "ISO 14001"], "richtig": 0},
    {"text": "Hauptziel des Qualitätsmanagements?", "optionen": ["Nacharbeit erhöhen", "Kundenorientierung & Fehlervermeidung", "Dokumentation minimieren"], "richtig": 1},
    {"text": "Ziel der 'Check'-Phase im PDCA?", "optionen": ["Umsetzen", "Ergebnisse analysieren", "Standardisieren"], "richtig": 1},
    {"text": "Wofür wird FMEA eingesetzt?", "optionen": ["Finanzplanung", "Früherkennung potenzieller Fehler", "Netzplanerstellung"], "richtig": 1},
    {"text": "Maßnahme in der 'Act'-Phase?", "optionen": ["Schulung entwickeln", "Ergebnisse vergleichen", "Erfolgreiche Arbeitsanweisung verbindlich einführen"], "richtig": 2},
    {"text": "Was bedeutet KVP?", "optionen": ["Kostenvergleichsprozess", "Kontinuierlicher Verbesserungsprozess", "Kreativitäts-Verfahren"], "richtig": 1},
    {"text": "Welche Dimension gehört zur Qualität?", "optionen": ["Nur Funktionalität", "Zuverlässigkeit, Benutzerfreundlichkeit, Sicherheit", "Nur der Preis"], "richtig": 1},
    {"text": "Was ist eine 'Qualitätsrichtlinie'?", "optionen": ["Dokument mit Qualitätszielen", "Testplan", "Budget"], "richtig": 0},
    {"text": "Was ist ein 'Audit'?", "optionen": ["Systematische Prüfung", "Fehlerbehebung", "Schulung"], "richtig": 0},
    {"text": "Was ist 'Zero Defects'?", "optionen": ["Fehlerfreiheit", "Viele Fehler", "Dokumentation"], "richtig": 0},
    {"text": "Was ist 'Total Quality Management'?", "optionen": ["Umfassendes QM", "Nur Produktqualität", "ISO 9000"], "richtig": 0},
    {"text": "Was ist ein 'Qualitätszirkel'?", "optionen": ["Mitarbeitergruppe zur Verbesserung", "Audit", "Testteam"], "richtig": 0},
    {"text": "Was ist 'Fehlerkosten'?", "optionen": ["Nacharbeit, Garantie, Vertrauensverlust", "Prüfkosten", "Planungskosten"], "richtig": 0},
    {"text": "Was ist 'Prüfkosten'?", "optionen": ["Tests und Audits", "Fehlerkosten", "Vermeidungskosten"], "richtig": 0},
    {"text": "Was ist 'Vermeidungskosten'?", "optionen": ["Schulungen, Prozessverbesserung", "Fehlerkosten", "Prüfkosten"], "richtig": 0},
    {"text": "Was ist ein 'Qualitätsmanagementhandbuch'?", "optionen": ["Beschreibt QM-System", "Projektplan", "Testhandbuch"], "richtig": 0},
    {"text": "Was ist die 'Deming-Kette'?", "optionen": ["Qualität → Produktivität → Marktanteil", "Kostenreduktion", "Zeitplanung"], "richtig": 0},
    {"text": "Was ist 'Six Sigma'?", "optionen": ["Fehlerreduzierung (DMAIC)", "ISO 9000", "PDCA"], "richtig": 0},
    {"text": "Was ist 'Lean Management'?", "optionen": ["Verschwendung reduzieren", "Mehr Kontrolle", "Lange Zyklen"], "richtig": 0},
    {"text": "Was ist 'Kaizen'?", "optionen": ["Kontinuierliche Verbesserung", "Großer Sprung", "Audit"], "richtig": 0},
    {"text": "Was ist ein 'Qualitätsplan'?", "optionen": ["Geplante QA-Aktivitäten", "Testplan", "Projektplan"], "richtig": 0},
    {"text": "Was ist ein 'Testfall'?", "optionen": ["Eingabe, Aktion, erwartetes Ergebnis", "Fehlerbericht", "User Story"], "richtig": 0},
    {"text": "Was ist 'Regressionstest'?", "optionen": ["Test nach Änderungen", "Ersttest", "Modultest"], "richtig": 0},
    {"text": "Was ist 'Akzeptanztest'?", "optionen": ["Test durch Kunden", "Entwicklertest", "Integrationstest"], "richtig": 0},
    {"text": "Was ist 'ISO 9004'?", "optionen": ["Leitfaden für nachhaltigen Erfolg", "Zertifizierungsnorm", "Begriffe"], "richtig": 0},
    {"text": "Was sind die sieben QM-Grundsätze?", "optionen": ["Kundenorientierung, Führung, Einbindung, Prozessansatz, Verbesserung, faktenbasierte Entscheidung, Beziehungsmanagement", "PDCA, FMEA, Six Sigma", "Planung, Steuerung, Abschluss"], "richtig": 0},
    {"text": "Was ist 'Qualitätssicherung'?", "optionen": ["Fehlervermeidung", "Produktprüfung", "Audit"], "richtig": 0},
    {"text": "Was ist 'Qualitätskontrolle'?", "optionen": ["Produktprüfung und Messung", "Prozessverbesserung", "Planung"], "richtig": 0},
    {"text": "Was ist ein 'Qualitätsaudit'?", "optionen": ["Untersuchung des QM-Systems", "Test", "Review"], "richtig": 0},
]

# ------------------------------------------------------------
# THEMA 8 – CHANGE MANAGEMENT (30 Fragen)
# ------------------------------------------------------------
thema8_zusammenfassung = (
    "**Was ist Change Management?**\n"
    "Change Management (Veränderungsmanagement) ist der strukturierte Prozess, um Menschen, Teams und Organisationen von einem aktuellen Zustand in einen angestrebten Zukunftszustand zu führen. Es ist besonders wichtig bei Projekten, da Projekte immer Veränderungen auslösen.\n\n"
    "**Warum ist Change Management wichtig?**\n"
    "• **Widerstände reduzieren**: Menschen neigen dazu, an Gewohntem festzuhalten. Ohne geplantes Change Management scheitern viele Projekte an mangelnder Akzeptanz.\n"
    "• **Nachhaltigkeit sichern**: Ein neues System oder ein neuer Prozess nützt nichts, wenn die Anwender ihn nicht annehmen.\n"
    "• **Erfolgsquote erhöhen**: Studien zeigen, dass Projekte mit professionellem Change Management signifikant häufiger ihre Ziele erreichen.\n\n"
    "**Die 8 Stufen des Wandels nach Kotter**\n"
    "1. **Dringlichkeit erzeugen** – Warum müssen wir uns ändern? (Krise oder Chance aufzeigen)\n"
    "2. **Führungskoalition aufbauen** – Ein starkes Team von Entscheidern formen\n"
    "3. **Vision und Strategie entwickeln** – Ein klares Bild der Zukunft zeichnen\n"
    "4. **Vision kommunizieren** – Immer wieder, auf allen Kanälen, vorleben\n"
    "5. **Hindernisse aus dem Weg räumen** – Prozesse, Strukturen, fehlende Fähigkeiten\n"
    "6. **Kurzfristige Erfolge schaffen** – Sichtbare Quick Wins erzeugen und feiern\n"
    "7. **Erfolge konsolidieren und weitere Veränderungen einleiten** – Nicht nachlassen\n"
    "8. **Veränderung in der Kultur verankern** – Neue Verhaltensweisen zur Normalität machen\n\n"
    "**Widerstand verstehen und managen**\n"
    "Widerstand ist normal und nicht unbedingt negativ. Er kann auf rationale Bedenken, emotionale Ängste oder Gewohnheit zurückgehen. Erfolgreiches Change Management hört zu, bezieht Betroffene frühzeitig ein, kommuniziert offen und bietet Qualifizierung und Unterstützung an.\n\n"
    "**Rollen im Change Management**\n"
    "• **Change Sponsor** – Führungskraft, die die Veränderung aktiv unterstützt und Ressourcen bereitstellt.\n"
    "• **Change Agent** – Die Person(en), die den Veränderungsprozess vorantreiben (häufig der Projektleiter oder ein spezieller Change Manager).\n"
    "• **Betroffene** – Die Mitarbeiter, deren Arbeitsalltag sich ändert.\n\n"
    "**Technisches Änderungsmanagement (Change Control)** – der formelle Prozess für Änderungen an Projektspezifikationen\n"
    "Während sich das organisatorische Change Management um die Menschen kümmert, regelt das **technische Change Control** den Umgang mit Änderungen an Projektzielen, Anforderungen, Budget, Terminen oder technischen Spezifikationen. Ziel ist es, unkontrollierte Ausweitungen (Scope Creep) zu vermeiden und nur genehmigte Änderungen umzusetzen.\n"
    "Typischer Ablauf eines Change Control Prozesses:\n"
    "• **Änderungsantrag (Change Request)** – Eine formelle Anfrage, die beschreibt, was geändert werden soll, warum und welche Auswirkungen erwartet werden.\n"
    "• **Analyse** – Bewertung der Auswirkungen auf Zeit, Kosten, Qualität, Ressourcen und Risiken.\n"
    "• **Entscheidung durch das Change Control Board (CCB)** – Ein Gremium aus Projektleiter, Auftraggeber, Fachbereichsvertretern und ggf. Spezialisten. Das CCB genehmigt, lehnt ab oder verschiebt den Antrag.\n"
    "• **Dokumentation und Umsetzung** – Genehmigte Änderungen werden dokumentiert, in den Projektplan eingepflegt und umgesetzt.\n"
    "• **Nachverfolgung** – Überprüfung, ob die Änderung den gewünschten Effekt erzielt hat.\n\n"
    "**Change Control Board (CCB)** – Zusammensetzung und Aufgaben\n"
    "Das CCB ist ein fester Bestandteil des Änderungsmanagements. Es tagt regelmäßig oder bei Bedarf. Typische Mitglieder: Projektleiter, Auftraggeber, technische Experten, Qualitätsmanager, Benutzervertreter. Entscheidungen werden oft nach dem Vier‑Augen‑Prinzip oder per Mehrheitsentscheid getroffen.\n\n"
    "**Unterschied: organisatorisches Change Management vs. technisches Change Control**\n"
    "• **Organisatorisches CM** (Ihr bisheriger Fokus) – Wie bringe ich die Menschen dazu, die Veränderung anzunehmen?\n"
    "• **Technisches Change Control** – Wie stelle ich sicher, dass Änderungen an den Projektspezifikationen kontrolliert und dokumentiert werden?\n"
    "Beide Aspekte sind für den Projekterfolg entscheidend. Fehlt das technische Change Control, geraten Projekte schnell in Zeit‑ und Kostenverzug durch ständige, ungeprüfte Änderungswünsche.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• Change Management = strukturierter Prozess, Menschen durch Veränderung zu führen (organisatorisch)\n"
    "• Kotter 8 Stufen = Dringlichkeit, Führungskoalition, Vision, Kommunikation, Hindernisse beseitigen, Quick Wins, Erfolge konsolidieren, Kultur verankern\n"
    "• Quick Win = sichtbarer früher Erfolg\n"
    "• Widerstand = normal, kann rationale oder emotionale Gründe haben\n"
    "• Change Sponsor = Führungskraft, die Veränderung aktiv unterstützt\n"
    "• Change Agent = treibt den Veränderungsprozess voran\n"
    "• Betroffene = Mitarbeiter, deren Arbeit sich ändert\n"
    "• PM vs. CM = PM steuert Technik, CM die menschliche Seite\n"
    "• Unfreeze‑Change‑Refreeze = Kurt‑Lewin‑Modell\n"
    "• ADKAR = Awareness, Desire, Knowledge, Ability, Reinforcement (individuelles CM)\n"
    "• Change Readiness Assessment = Bewertung der Veränderungsbereitschaft\n"
    "• Change Impact Analysis = Analyse der Auswirkungen auf Menschen und Prozesse\n"
    "• Pilot = Test der Veränderung in kleinem Bereich\n"
    "• Change Fatigue = Ermüdung durch zu viele Veränderungen\n"
    "• **Technisches Change Control** = formeller Prozess zur Steuerung von Änderungen an Projektspezifikationen\n"
    "• **Change Request** = formeller Änderungsantrag\n"
    "• **Change Control Board (CCB)** = Gremium zur Entscheidung über Änderungsanträge\n"
    "• **Scope Creep** = unkontrollierte Ausweitung des Projektumfangs (wird durch Change Control verhindert)"
)

thema8_fragen = [
    {"text": "Hauptziel von Change Management?", "optionen": ["Technische Umsetzung", "Menschen durch Veränderung führen", "Budget optimieren"], "richtig": 1},
    {"text": "Warum scheitern viele Projekte ohne CM?", "optionen": ["Technik versagt", "Mangelnde Akzeptanz und Widerstände", "Zeitplan zu knapp"], "richtig": 1},
    {"text": "Nach Kotter: Was ist der erste Schritt?", "optionen": ["Vision entwickeln", "Dringlichkeit erzeugen", "Kurzfristige Erfolge"], "richtig": 1},
    {"text": "Was ist ein 'Quick Win'?", "optionen": ["Budgetkürzung", "Sichtbarer früher Erfolg", "Kündigung von Widerständlern"], "richtig": 1},
    {"text": "Welche Aussage über Widerstand ist richtig?", "optionen": ["Immer negativ", "Normal, kann rationale oder emotionale Gründe haben", "Kommt nur von unfähigen Mitarbeitern"], "richtig": 1},
    {"text": "Unterschied PM vs. CM?", "optionen": ["PM kümmert sich um Menschen, CM um Technik", "PM steuert technische Umsetzung, CM die menschliche Seite", "Gibt keinen Unterschied"], "richtig": 1},
    {"text": "Was ist ein Change Sponsor?", "optionen": ["Externer Berater", "Führungskraft, die die Veränderung aktiv unterstützt", "Ein Teammitglied"], "richtig": 1},
    {"text": "Welche Stufe folgt auf 'Dringlichkeit erzeugen' bei Kotter?", "optionen": ["Vision entwickeln", "Führungskoalition aufbauen", "Kurzfristige Erfolge"], "richtig": 1},
    {"text": "Was ist ein 'Change Agent'?", "optionen": ["Person, die den Veränderungsprozess vorantreibt", "Externer Prüfer", "Gegner der Veränderung"], "richtig": 0},
    {"text": "Was ist 'Betroffenheit' im Change Management?", "optionen": ["Mitarbeiter, deren Arbeit sich ändert", "Führungskräfte", "Kunden"], "richtig": 0},
    {"text": "Was ist der Unterschied zwischen organisatorischem Change Management und technischem Change Control?", "optionen": ["Organisatorisches CM kümmert sich um Budget, technisches Change Control um Zeitpläne", "Organisatorisches CM fokussiert auf die Menschen und Akzeptanz, technisches Change Control auf kontrollierte Änderungen an Projektspezifikationen", "Es gibt keinen Unterschied – beides ist dasselbe"], "richtig": 1},
    {"text": "Welche Kommunikationsform ist im Change Management wichtig?", "optionen": ["Transparente, wiederholte Kommunikation", "Einmalige E-Mail", "Geheimhaltung"], "richtig": 0},
    {"text": "Was ist ein 'Change Readiness Assessment'?", "optionen": ["Bewertung der Veränderungsbereitschaft", "Budgetanalyse", "Risikoanalyse"], "richtig": 0},
    {"text": "Was ist ein 'Change Impact Analysis'?", "optionen": ["Analyse der Auswirkungen der Veränderung", "Kostenanalyse", "Zeitplan"], "richtig": 0},
    {"text": "Was ist ein 'Change Management Plan'?", "optionen": ["Dokument mit Maßnahmen zur Unterstützung der Veränderung", "Projektplan", "Kommunikationsplan"], "richtig": 0},
    {"text": "Was ist ein 'Resistance Management'?", "optionen": ["Umgang mit Widerständen", "Ignorieren", "Bestrafen"], "richtig": 0},
    {"text": "Was ist 'Partizipation' im Change Management?", "optionen": ["Einbeziehen der Betroffenen", "Top-down-Anweisung", "Externe Beratung"], "richtig": 0},
    {"text": "Was ist 'Emotionale Reaktion' auf Veränderung?", "optionen": ["Kubler-Ross Trauerkurve", "Wut", "Freude"], "richtig": 0},
    {"text": "Was ist ein 'Change Network'?", "optionen": ["Gruppe von Multiplikatoren", "Soziales Netzwerk", "IT-System"], "richtig": 0},
    {"text": "Welche Aufgabe hat das Change Control Board (CCB)?", "optionen": ["Es kümmert sich um die Kommunikation mit den Stakeholdern", "Es entscheidet über die Annahme, Ablehnung oder Verschiebung von Änderungsanträgen", "Es erstellt den Projektstrukturplan"], "richtig": 1},
    {"text": "Was ist 'Kulturwandel'?", "optionen": ["Nachhaltige Veränderung von Werten", "Prozessänderung", "Umstrukturierung"], "richtig": 0},
    {"text": "Was ist ein 'Pilot' im Change Management?", "optionen": ["Test in kleinem Bereich", "Komplettumstellung", "Schulung"], "richtig": 0},
    {"text": "Was ist 'Change Kommunikation'?", "optionen": ["Zielgerichtete Information", "Allgemeine Unternehmenskommunikation", "Marketing"], "richtig": 0},
    {"text": "Was ist ein 'Change-Controlling'?", "optionen": ["Überwachung des Fortschritts der Veränderung", "Budgetkontrolle", "Terminplanung"], "richtig": 0},
    {"text": "Was ist 'Nachhaltigkeit von Veränderungen'?", "optionen": ["Verankerung in der Organisation", "Kurzer Effekt", "Dokumentation"], "richtig": 0},
    {"text": "Was ist 'Widerstandsursache'?", "optionen": ["Angst vor Verlust", "Faulheit", "Unfähigkeit"], "richtig": 0},
    {"text": "Was ist 'Change Capability'?", "optionen": ["Fähigkeit zur Veränderung", "Finanzkraft", "Technologie"], "richtig": 0},
    {"text": "Was ist 'Change Leadership'?", "optionen": ["Führungsstil, der Veränderungen vorantreibt", "Management von Budget", "Planung"], "richtig": 0},
    {"text": "Was ist ein 'Change Story'?", "optionen": ["Überzeugende Erzählung über die Veränderung", "Anekdote", "Bericht"], "richtig": 0},
    {"text": "Was ist ein ‚Change Request‘?", "optionen": ["Ein formeller Antrag auf Änderung von Projektzielen, Budget, Terminen oder technischen Spezifikationen", "Eine informelle E-Mail mit einer neuen Idee", "Die Zustimmung des Auftraggebers zur nächsten Phase"], "richtig": 0},
]

# ------------------------------------------------------------
# THEMA 9 – PROJEKTCONTROLLING & BERICHT (30 Fragen)
# ------------------------------------------------------------
thema9_zusammenfassung = (
    "**Was ist Projektcontrolling?**\n"
    "Das Projektcontrolling umfasst alle Aktivitäten zur **Planung, Überwachung und Steuerung** von Projektzielen – insbesondere Termine, Kosten, Ressourcen und Qualität. Es liefert die Grundlage für Entscheidungen des Projektleiters und des Lenkungsausschusses.\n\n"
    "**Wichtige Kennzahlen und Methoden**\n"
    "• **Soll-Ist-Vergleich**: Gegenüberstellung der geplanten und tatsächlichen Werte (z.B. Termine, Kosten, Arbeitsstunden).\n"
    "• **Earned Value Management (EVM)**: Integrierte Methode, die Termin- und Kostenabweichungen gleichzeitig erfasst:\n"
    "   - **Planned Value (PV)**: Geplanter Wert zum Zeitpunkt.\n"
    "   - **Earned Value (EV)**: Tatsächlich erbrachter Wert.\n"
    "   - **Actual Cost (AC)**: Tatsächlich angefallene Kosten.\n"
    "   - **Cost Performance Index (CPI) = EV / AC** – Kosteneffizienz (CPI < 1 = zu teuer).\n"
    "   - **Schedule Performance Index (SPI) = EV / PV** – Termineffizienz (SPI < 1 = im Zeitverzug).\n\n"
    "**Beispielrechnung:**\n"
    "Gesamtbudget (BAC) = 100.000 €. Nach 4 Wochen (Statusdatum):\n"
    "   - PV = 40.000 € (40% der Arbeit sollten laut Plan erledigt sein).\n"
    "   - EV = 35.000 € (tatsächlicher Fortschritt).\n"
    "   - AC = 45.000 € (tatsächliche Kosten).\n"
    "   - CPI = 35.000 / 45.000 = 0,78 (22% Kostenüberschreitung).\n"
    "   - SPI = 35.000 / 40.000 = 0,875 (12,5% Zeitverzug).\n\n"
    "**Forecasting (Prognose)**\n"
    "Aus den bisherigen Daten wird die voraussichtliche Enddauer und der voraussichtliche Endaufwand berechnet:\n"
    "   • **Estimate at Completion (EAC)** = Gesamtbudget / CPI (falls aktuelle Effizienz anhält).\n"
    "   • **Estimate to Complete (ETC)** = EAC – AC (noch benötigte Mittel).\n\n"
    "**Berichtswesen**\n"
    "Regelmäßige Berichte an Stakeholder sorgen für Transparenz. Typische Berichte:\n"
    "• **Statusbericht** (wöchentlich/monatlich): Fortschritt, nächste Meilensteine, Risiken, Maßnahmen.\n"
    "• **Ampelbericht** (rot/gelb/grün) für schnellen Überblick über Termin, Kosten, Qualität.\n"
    "• **Meilensteintrendanalyse** – visuelle Darstellung von Abweichungen der Meilensteintermine.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• Projektcontrolling = Planung, Überwachung, Steuerung von Terminen, Kosten, Ressourcen\n"
    "• Soll‑Ist‑Vergleich = Abweichungen zwischen Plan und tatsächlichen Werten\n"
    "• PV (Planned Value) = geplanter Wert bis zum Zeitpunkt\n"
    "• EV (Earned Value) = tatsächlich erbrachter Wert der geleisteten Arbeit\n"
    "• AC (Actual Cost) = tatsächliche Kosten\n"
    "• CV (Cost Variance) = EV – AC\n"
    "• SV (Schedule Variance) = EV – PV\n"
    "• CPI (Cost Performance Index) = EV / AC (<1 = teurer, >1 = günstiger)\n"
    "• SPI (Schedule Performance Index) = EV / PV (<1 = Zeitverzug, >1 = vor Plan)\n"
    "• EAC (Estimate at Completion) = voraussichtliche Gesamtkosten am Ende\n"
    "• ETC (Estimate to Complete) = noch benötigte Mittel (EAC – AC)\n"
    "• Statusbericht = Fortschritt, Meilensteine, Risiken, Maßnahmen\n"
    "• Ampelbericht = rot/gelb/grün für schnellen Überblick\n"
    "• Meilensteintrendanalyse = Diagramm mit geplanten vs. tatsächlichen Terminen\n"
    "• Earned Schedule = Weiterentwicklung von EVM für reine Zeitanalyse\n"
    "• TCPI (To Complete Performance Index) = benötigte Effizienz für Restarbeit\n"
)

thema9_fragen = [
    {"text": "Hauptziel des Projektcontrollings?", "optionen": ["Technische Entwicklung", "Planung, Überwachung und Steuerung von Terminen, Kosten, Ressourcen", "Teammotivation"], "richtig": 1},
    {"text": "Was ist der Earned Value (EV)?", "optionen": ["Geplante Kosten", "Tatsächlich erbrachter Wert der geleisteten Arbeit", "Tatsächliche Kosten"], "richtig": 1},
    {"text": "CPI von 0,8 bedeutet?", "optionen": ["Günstiger als geplant", "Teurer als geplant (80% Effizienz)", "Termingerecht"], "richtig": 1},
    {"text": "Wofür steht SPI?", "optionen": ["Termineffizienz (EV/PV)", "Kosteneffizienz (EV/AC)", "Qualitätsindex"], "richtig": 0},
    {"text": "Welcher Bericht nutzt eine Ampel?", "optionen": ["Meilensteintrendanalyse", "Statusbericht mit Ampel", "Projektstrukturplan"], "richtig": 1},
    {"text": "Was ist die EAC (Estimate at Completion)?", "optionen": ["Geplante Dauer", "Voraussichtliche Gesamtkosten am Ende", "Bisher ausgegebene Kosten"], "richtig": 1},
    {"text": "Was zeigt der Soll-Ist-Vergleich?", "optionen": ["Nur die Kosten", "Abweichungen zwischen Plan und tatsächlichen Werten", "Nur die Termine"], "richtig": 1},
    {"text": "Was ist ein typischer Inhalt eines Statusberichts?", "optionen": ["Nur geleistete Stunden", "Fortschritt, nächste Meilensteine, Risiken, Maßnahmen", "Nur Budget"], "richtig": 1},
    {"text": "Was ist der Planned Value (PV)?", "optionen": ["Geplanter Wert der bis zu einem Zeitpunkt abgeschlossenen Arbeit", "Tatsächlicher Wert", "Kosten"], "richtig": 0},
    {"text": "Was ist der Actual Cost (AC)?", "optionen": ["Tatsächliche Kosten", "Geplante Kosten", "Erbrachter Wert"], "richtig": 0},
    {"text": "Was ist die Cost Variance (CV)?", "optionen": ["EV - AC", "EV - PV", "AC - PV"], "richtig": 0},
    {"text": "Was ist die Schedule Variance (SV)?", "optionen": ["EV - PV", "EV - AC", "PV - AC"], "richtig": 0},
    {"text": "Was bedeutet CPI > 1?", "optionen": ["Kosteneffizient (unter Budget)", "Über Budget", "Planmäßig"], "richtig": 0},
    {"text": "Was bedeutet SPI < 1?", "optionen": ["Im Zeitverzug", "Vor dem Zeitplan", "Planmäßig"], "richtig": 0},
    {"text": "Was ist ein 'Forecast'?", "optionen": ["Prognose", "Rückblick", "Budget"], "richtig": 0},
    {"text": "Was ist ETC (Estimate to Complete)?", "optionen": ["Geschätzte restliche Kosten", "Gesamtkosten", "Bisherige Kosten"], "richtig": 0},
    {"text": "Was ist eine 'Meilensteintrendanalyse'?", "optionen": ["Diagramm mit geplanten vs. tatsächlichen Terminen", "Gantt", "Netzplan"], "richtig": 0},
    {"text": "Was ist ein 'Projektcontrolling-Board'?", "optionen": ["Dashboard mit Kennzahlen", "Lenkungsausschuss", "Bericht"], "richtig": 0},
    {"text": "Was ist 'Earned Schedule'?", "optionen": ["Weiterentwicklung von EVM für Zeitanalyse", "Kostenanalyse", "Qualität"], "richtig": 0},
    {"text": "Was ist ein 'Kosten-Bericht'?", "optionen": ["Geplante vs. tatsächliche Kosten", "Terminbericht", "Risikobericht"], "richtig": 0},
    {"text": "Was ist ein 'Ressourcenbericht'?", "optionen": ["Auslastung der Ressourcen", "Kosten", "Termine"], "richtig": 0},
    {"text": "Was ist 'Projektcontrolling' in der Initiierungsphase?", "optionen": ["Aufwandsschätzung, Wirtschaftlichkeitsrechnung", "Detailplanung", "Abnahme"], "richtig": 0},
    {"text": "Was ist ein 'Business Case Review'?", "optionen": ["Überprüfung der Wirtschaftlichkeit während des Projekts", "Projektstart", "Projektende"], "richtig": 0},
    {"text": "Was ist ein 'Change Request' im Controlling?", "optionen": ["Formeller Antrag auf Änderung von Budget, Termin oder Umfang", "Fehler", "Neue Idee"], "richtig": 0},
    {"text": "Was ist 'Varianzanalyse'?", "optionen": ["Untersuchung der Ursachen von Abweichungen", "Berechnung von Kennzahlen", "Prognose"], "richtig": 0},
    {"text": "Was ist 'Trendanalyse'?", "optionen": ["Analyse über Zeit", "Einmalige Berechnung", "Budget"], "richtig": 0},
    {"text": "Was ist ein 'Projekt-Dashboard'?", "optionen": ["Visuelle KPIs", "Ausführlicher Bericht", "Zeitplan"], "richtig": 0},
    {"text": "Was ist 'Earned Value Management'?", "optionen": ["Integrierte Methode für Kosten- und Zeitkontrolle", "Qualitätsmethode", "Risikomethode"], "richtig": 0},
    {"text": "Was ist die 'Budget at Completion' (BAC)?", "optionen": ["Gesamtbudget", "Bisherige Kosten", "Restbudget"], "richtig": 0},
    {"text": "Was ist die 'To Complete Performance Index' (TCPI)?", "optionen": ["Benötigte Effizienz für Restarbeit", "Aktuelle Effizienz", "Terminindex"], "richtig": 0},
]

# ------------------------------------------------------------
# THEMA 10 – PROJEKTVORBEREITUNG & MACHBARKEIT (30 Fragen)
# ------------------------------------------------------------
thema10_zusammenfassung = (
    "**Projektvorbereitung – der erfolgreiche Start**\n"
    "Bevor ein Projekt beginnt, müssen zwei zentrale Dokumente erstellt werden: die **Machbarkeitsstudie** und die **Stakeholderanalyse**. Beide sind Grundlage für die Entscheidung, ob und wie das Projekt durchgeführt wird.\n\n"
    "**Machbarkeitsstudie** (auch ‚Feasibility Study‘) untersucht, ob ein Projekt unter den gegebenen Rahmenbedingungen realisierbar ist. Sie beantwortet die Frage: ‚Sollten wir das Projekt machen?‘\n"
    "Typische Analysebereiche einer Machbarkeitsstudie:\n"
    "• **Technische Machbarkeit** – Stehen die notwendigen Technologien, Werkzeuge und Kenntnisse zur Verfügung?\n"
    "• **Wirtschaftliche Machbarkeit** – Ist das Projekt finanziell sinnvoll? (Investition, Einsparungen, erwartete Erträge)\n"
    "• **Rechtliche Machbarkeit** – Gibt es gesetzliche Hürden, Genehmigungspflichten, Vertragsrisiken?\n"
    "• **Betrieblicher Nutzen** – Löst das Projekt das eigentliche Problem? Wie verbessert es die Abläufe?\n"
    "• **Ressourcenverfügbarkeit** – Sind die benötigten Mitarbeiter, Budgets, Materialien und Infrastruktur vorhanden?\n"
    "• **Zeitliche Machbarkeit** – Kann das Projekt in einem vertretbaren Zeitrahmen abgeschlossen werden?\n"
    "• **Optional: Marktanalyse** – Bei neuen Produkten: Gibt es einen Markt? Wer sind die Konkurrenten?\n\n"
    "Das Ergebnis einer Machbarkeitsstudie ist eine **Empfehlung** (durchführen / nicht durchführen / mit Auflagen) und die Grundlage für den **Projektauftrag**.\n\n"
    "**Stakeholderanalyse** – Wer ist betroffen und wie?\n"
    "Stakeholder sind Personen oder Gruppen, die ein berechtigtes Interesse am Projekt haben oder von seinen Ergebnissen beeinflusst werden. Die Analyse umfasst drei Schritte:\n"
    "1. **Identifizieren**: Wer sind die Stakeholder? (Kunde, Endnutzer, Management, Lieferanten, Behörden, …)\n"
    "2. **Priorisieren**: Ordnen Sie die Stakeholder nach **Einfluss (Macht)** und **Interesse (Betroffenheit)**. Typische Matrix:\n"
    "   - **Hoher Einfluss + hohes Interesse** → eng einbinden, regelmäßig informieren\n"
    "   - **Hoher Einfluss + niedriges Interesse** → zufriedenstellen, auf dem Laufenden halten\n"
    "   - **Niedriger Einfluss + hohes Interesse** → informieren, ihre Bedürfnisse berücksichtigen\n"
    "   - **Niedriger Einfluss + niedriges Interesse** → nur beobachten\n"
    "3. **Verstehen**: Welche Erwartungen, Motive und Befürchtungen haben die Stakeholder? Wie können negative Einflüsse abgemildert werden?\n\n"
    "**Risikomatrix** (Vorschau) – Ein Werkzeug, um Risiken nach **Eintrittswahrscheinlichkeit** und **Auswirkung** zu bewerten. Sie wird später in der Projektplanung genutzt, um die wichtigsten Risiken zu identifizieren und Gegenmaßnahmen zu planen.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• Machbarkeitsstudie = Untersuchung der technischen, wirtschaftlichen, rechtlichen, betrieblichen, ressourcenbezogenen und zeitlichen Machbarkeit eines Projekts\n"
    "• Stakeholder = Person oder Gruppe mit Interesse am Projekt\n"
    "• Stakeholderanalyse = Identifikation, Priorisierung (Einfluss/Interesse) und Verständnis der Stakeholder\n"
    "• Risikomatrix = Diagramm zur Bewertung von Risiken nach Eintrittswahrscheinlichkeit und Schadensauswirkung\n"
    "• Technische Machbarkeit = Verfügbarkeit von Technologien und Fachwissen\n"
    "• Wirtschaftliche Machbarkeit = Kosten-Nutzen-Verhältnis, Amortisation, Rentabilität\n"
    "• Rechtliche Machbarkeit = Einhaltung von Gesetzen, Verträgen, Genehmigungen\n"
    "• Betrieblicher Nutzen = Verbesserung der Arbeitsabläufe, Effizienzsteigerung\n"
    "• Ressourcenverfügbarkeit = Personal, Budget, Material, Infrastruktur vorhanden?\n"
    "• Zeitliche Machbarkeit = realistische Projektdauer"
)

thema10_fragen = [
    {"text": "Was ist das primäre Ziel einer Machbarkeitsstudie?", "optionen": ["Den Projektplan detailliert auszuarbeiten", "Zu prüfen, ob ein Projekt realisierbar ist und sich lohnt", "Das Budget für das Projekt festzulegen"], "richtig": 1},
    {"text": "Welcher Bereich der Machbarkeitsstudie untersucht, ob die benötigten Mitarbeiter und Materialien vorhanden sind?", "optionen": ["Technische Machbarkeit", "Rechtliche Machbarkeit", "Ressourcenverfügbarkeit"], "richtig": 2},
    {"text": "In der Stakeholderanalyse: Welche Stakeholder sollten nach der Einfluss-Interesse-Matrix ‚eng einbezogen und regelmäßig informiert‘ werden?", "optionen": ["Hoher Einfluss + hohes Interesse", "Hoher Einfluss + niedriges Interesse", "Niedriger Einfluss + hohes Interesse"], "richtig": 0},
    {"text": "Wozu dient eine Risikomatrix?", "optionen": ["Zur Darstellung von Projektmeilensteinen", "Zur Bewertung von Risiken nach Eintrittswahrscheinlichkeit und Auswirkung", "Zur Priorisierung von Stakeholdern"], "richtig": 1},
    {"text": "Welche Frage beantwortet die wirtschaftliche Machbarkeit?", "optionen": ["Stehen die Technologien zur Verfügung?", "Ist das Projekt finanziell sinnvoll?", "Sind gesetzliche Hürden zu erwarten?"], "richtig": 1},
    {"text": "Was ist der erste Schritt einer Stakeholderanalyse?", "optionen": ["Priorisierung der Stakeholder", "Verstehen der Motive", "Identifikation aller Stakeholder"], "richtig": 2},
    {"text": "Welche Aussage zur rechtlichen Machbarkeit ist richtig?", "optionen": ["Sie prüft die Verfügbarkeit von Rechtsanwälten", "Sie untersucht gesetzliche Hürden und Genehmigungspflichten", "Sie bewertet die Rechtsform des Unternehmens"], "richtig": 1},
    {"text": "Ein Projekt ist technisch machbar, wenn ...", "optionen": ["das Budget ausreicht", "die notwendigen Technologien und Fachkenntnisse vorhanden sind", "die gesetzlichen Vorschriften eingehalten werden können"], "richtig": 1},
    {"text": "Welches Ergebnis liefert eine Machbarkeitsstudie typischerweise?", "optionen": ["Einen detaillierten Projektstrukturplan", "Eine Empfehlung (durchführen / nicht durchführen / mit Auflagen)", "Einen rechtsverbindlichen Vertrag"], "richtig": 1},
    {"text": "Was versteht man unter ‚betrieblichem Nutzen‘ in der Machbarkeitsstudie?", "optionen": ["Die Steigerung des Aktienkurses", "Die Verbesserung der Arbeitsabläufe und Effizienz", "Die Reduzierung der Mitarbeiterzahl"], "richtig": 1},
    {"text": "Welche Stakeholder haben in der Einfluss-Interesse-Matrix niedrigen Einfluss aber hohes Interesse?", "optionen": ["Eng einbeziehen", "Informieren und Bedürfnisse berücksichtigen", "Nur beobachten"], "richtig": 1},
    {"text": "Was ist das Ziel der dritten Phase der Stakeholderanalyse (Verstehen)?", "optionen": ["Eine Liste aller Stakeholder zu erstellen", "Erwartungen, Motive und Befürchtungen der Stakeholder zu analysieren", "Die Stakeholder nach Macht zu sortieren"], "richtig": 1},
    {"text": "Welche Aussage zur zeitlichen Machbarkeit trifft zu?", "optionen": ["Sie prüft, ob das Projekt zu einer beliebigen Zeit gestartet werden kann", "Sie untersucht, ob das Projekt in einem vertretbaren Zeitrahmen abschließbar ist", "Sie ist nur bei Projekten mit externen Terminvorgaben relevant"], "richtig": 1},
    {"text": "Eine Marktanalyse in der Machbarkeitsstudie ist besonders wichtig, wenn ...", "optionen": ["das Projekt ein völlig neues Produkt oder eine neue Dienstleistung betrifft", "die Ressourcen knapp sind", "das Projekt intern für die eigene IT-Abteilung durchgeführt wird"], "richtig": 0},
    {"text": "Was ist die Grundlage für den formellen Projektauftrag?", "optionen": ["Das Lastenheft", "Die Empfehlung der Machbarkeitsstudie", "Die Stellenausschreibung für den Projektleiter"], "richtig": 1},
    {"text": "Welche Dimension der Machbarkeit prüft die Einhaltung von DSGVO oder anderen Gesetzen?", "optionen": ["Technische Machbarkeit", "Rechtliche Machbarkeit", "Betrieblicher Nutzen"], "richtig": 1},
    {"text": "In der Risikomatrix werden Risiken üblicherweise nach welchen zwei Kriterien bewertet?", "optionen": ["Dauer und Kosten", "Eintrittswahrscheinlichkeit und Schadensauswirkung", "Verantwortlicher und Maßnahme"], "richtig": 1},
    {"text": "Wozu dient die Priorisierung von Stakeholdern?", "optionen": ["Um unliebsame Personen vom Projekt auszuschließen", "Um die Kommunikationsintensität auf die wichtigsten Stakeholder zu konzentrieren", "Um die Gehälter der Stakeholder zu bestimmen"], "richtig": 1},
    {"text": "Was ist keine typische Frage der technischen Machbarkeit?", "optionen": ["Gibt es die benötigte Software?", "Haben unsere Mitarbeiter die erforderlichen Kenntnisse?", "Wird der Kunde das Produkt kaufen?"], "richtig": 2},
    {"text": "Die wirtschaftliche Machbarkeit wird oft mit welcher Kennzahl bewertet?", "optionen": ["Return on Investment (ROI)", "Mean Time to Repair (MTTR)", "Story Points"], "richtig": 0},
    {"text": "Was gehört nicht zu den typischen Analysebereichen einer Machbarkeitsstudie?", "optionen": ["Kulturelle Machbarkeit", "Technische Machbarkeit", "Zeitliche Machbarkeit"], "richtig": 0},
    {"text": "Welche Stakeholder sollten in der Matrix nur ‚beobachtet‘ werden?", "optionen": ["Hoher Einfluss + hohes Interesse", "Niedriger Einfluss + niedriges Interesse", "Hoher Einfluss + niedriges Interesse"], "richtig": 1},
    {"text": "Was bedeutet ‚Auflagen‘ als Ergebnis einer Machbarkeitsstudie?", "optionen": ["Das Projekt wird nicht durchgeführt", "Das Projekt kann unter bestimmten Bedingungen (z.B. Budgetkürzung) durchgeführt werden", "Das Projekt wird sofort gestartet"], "richtig": 1},
    {"text": "Welche Rolle spielt der Projektauftraggeber bei der Machbarkeitsstudie?", "optionen": ["Er erstellt die Studie allein", "Er genehmigt die Studie und entscheidet auf Basis der Empfehlung", "Er hat keine Rolle"], "richtig": 1},
    {"text": "Was ist die erste Frage, die eine Machbarkeitsstudie beantworten sollte?", "optionen": ["Wie genau wird das Projekt umgesetzt?", "Sollte das Projekt überhaupt durchgeführt werden?", "Wer wird der Projektleiter sein?"], "richtig": 1},
    {"text": "Der Begriff ‚Feasibility Study‘ ist ein anderer Name für ...", "optionen": ["Machbarkeitsstudie", "Projektstrukturplan", "Risikoanalyse"], "richtig": 0},
    {"text": "Welches Dokument beschreibt die Anforderungen des Auftraggebers und wird oft parallel zur Machbarkeitsstudie erstellt?", "optionen": ["Pflichtenheft", "Lastenheft", "Projektauftrag"], "richtig": 1},
    {"text": "Warum ist die Stakeholderanalyse vor Projektbeginn wichtig?", "optionen": ["Um bereits vorab Konflikte mit wichtigen Gruppen zu erkennen und zu entschärfen", "Um die genauen Kosten zu berechnen", "Um den Projektnamen festzulegen"], "richtig": 0},
    {"text": "Welche Aussage zur Ressourcenverfügbarkeit ist richtig?", "optionen": ["Sie betrachtet nur die finanziellen Mittel", "Sie prüft, ob Personal, Budget, Material und Infrastruktur in ausreichender Menge und Qualität zur Verfügung stehen", "Sie ist identisch mit der technischen Machbarkeit"], "richtig": 1},
    {"text": "Was ist das Ergebnis einer Machbarkeitsstudie, wenn das Projekt nicht realisierbar ist?", "optionen": ["Trotzdem wird ein Projektauftrag erteilt", "Das Projekt wird abgelehnt oder zur Überarbeitung zurückgegeben", "Die Studie wird ignoriert"], "richtig": 1},
]

# ------------------------------------------------------------
# THEMA 11 – LEAN & AGILE METHODEN (VERTIEFUNG) (30 Fragen)
# ------------------------------------------------------------
thema11_zusammenfassung = (
    "**Lean Management – Verschwendung eliminieren, Wert maximieren**\n"
    "Lean entstand in der Produktion (Toyota) und wird heute auch in der IT und im Projektmanagement angewendet. Das Ziel ist, **Verschwendung (Waste)** zu reduzieren, die keinen Mehrwert für den Kunden schafft.\n\n"
    "**Die 7 Arten der Verschwendung (nach Taiichi Ohno) in der IT:**\n"
    "1. **Überproduktion** – Mehr Features entwickeln als benötigt; Dokumente schreiben, die nie gelesen werden.\n"
    "2. **Wartezeit** – Teams warten auf Entscheidungen, Freigaben, Lieferungen, Builds.\n"
    "3. **Transport** – Unnötige Übergabe von Informationen, Tickets, Code zwischen Teams.\n"
    "4. **Überbearbeitung** – Zu detaillierte Dokumentation, unnötige Optimierungen, Gold Plating.\n"
    "5. **Lagerhaltung** – Halbfertige Aufgaben, offene Tickets, nicht freigegebene Code-Änderungen.\n"
    "6. **Bewegung** – Häufiger Kontextwechsel, ineffiziente Meetings, Suchen von Informationen.\n"
    "7. **Fehler/Defekte** – Bugs, fehlerhafte Konfigurationen, Nacharbeit.\n\n"
    "**Kanban** – Visualisierung des Arbeitsflusses\n"
    "Ein Kanban-Board zeigt Spalten wie ‚To Do‘, ‚In Progress‘, ‚Done‘. Die Anzahl der gleichzeitig in Arbeit befindlichen Aufgaben (Work in Progress, WIP) wird begrenzt, um Engpässe sichtbar zu machen und den Durchsatz zu erhöhen.\n\n"
    "**Kaizen** – Kontinuierliche Verbesserung in kleinen Schritten\n"
    "Kaizen ist eine Philosophie, bei der **jeder Mitarbeiter** ständig kleine Verbesserungen vorschlägt und umsetzt. Es ist der Motor des kontinuierlichen Verbesserungsprozesses (KVP).\n\n"
    "**Extreme Programming (XP)** – Technische Exzellenz in agilen Teams\n"
    "XP ist eine agile Methode, die auf technische Praktiken setzt:\n"
    "• **Test-Driven Development (TDD)**: Schreiben Sie zuerst einen fehlschlagenden Test, dann den minimalen Code, um ihn zu bestehen, dann refaktorisieren.\n"
    "• **Pair Programming**: Zwei Entwickler arbeiten gemeinsam an einem Rechner – einer schreibt Code, der andere reviewt in Echtzeit.\n"
    "• **Einfaches Design** – Nur das Nötigste implementieren (YAGNI – You Ain‘t Gonna Need It).\n"
    "• **Kontinuierliche Integration (CI)** – Code wird mehrmals täglich in den Hauptzweig integriert.\n\n"
    "**DORA-Metriken – Leistung von DevOps-Teams messen**\n"
    "Die DevOps Research and Assessment (DORA) Gruppe definierte vier Kennzahlen, die Vorhersagekraft für die Teamleistung haben:\n"
    "1. **Deployment Frequency** – Wie oft wird in Produktion ausgeliefert? (hoch = gut)\n"
    "2. **Lead Time for Changes** – Zeit von Code-Commit bis Deployment in Produktion (kurz = gut)\n"
    "3. **Change Failure Rate** – Anteil der Deployments, die zu einem Fehler führen (niedrig = gut)\n"
    "4. **Time to Restore Service** – Zeit, um nach einem Ausfall wiederherzustellen (kurz = gut)\n"
    "Diese Metriken sind aussagekräftiger als die reine Velocity (Story Points pro Sprint), da sie sowohl Geschwindigkeit als auch Stabilität erfassen.\n\n"
    "---\n"
    "**Begriffsklärungen (kompakt):**\n"
    "• Lean = Managementphilosophie zur Vermeidung von Verschwendung\n"
    "• 7 Verschwendungen = Überproduktion, Wartezeit, Transport, Überbearbeitung, Lagerhaltung, Bewegung, Fehler\n"
    "• Kanban = visuelles Board mit WIP-Limits zur Steuerung des Arbeitsflusses\n"
    "• Kaizen = kontinuierliche Verbesserung in kleinen Schritten\n"
    "• Extreme Programming (XP) = agile Methode mit technischen Praktiken (TDD, Pair Programming, CI)\n"
    "• TDD = Test-Driven Development (Test → Code → Refaktor)\n"
    "• Pair Programming = zwei Entwickler an einem Rechner\n"
    "• DORA-Metriken = Deployment Frequency, Lead Time for Changes, Change Failure Rate, Time to Restore Service\n"
    "• Velocity = Story Points pro Sprint (nicht Teil von DORA, aber in Scrum üblich)"
)

thema11_fragen = [
    {"text": "Welches Ziel verfolgt Lean Management?", "optionen": ["Maximale Auslastung der Mitarbeiter", "Eliminierung von Verschwendung und Maximierung des Kundennutzens", "Detaillierte Dokumentation aller Prozesse"], "richtig": 1},
    {"text": "Was ist KEINE der sieben Verschwendungsarten nach Taiichi Ohno?", "optionen": ["Überproduktion", "Wartezeit", "Budgetüberschreitung"], "richtig": 2},
    {"text": "Welche Aussage beschreibt Kanban richtig?", "optionen": ["Ein starres Framework mit festen Rollen", "Visualisierung des Arbeitsflusses mit WIP-Limits", "Eine Methode zur Aufwandsschätzung"], "richtig": 1},
    {"text": "Was ist das Prinzip von Test-Driven Development (TDD)?", "optionen": ["Erst Code schreiben, dann testen", "Erst Test schreiben, dann Code, dann refaktorieren", "Code und Tests gleichzeitig schreiben"], "richtig": 1},
    {"text": "Welche DORA-Metrik misst, wie oft in Produktion ausgeliefert wird?", "optionen": ["Lead Time for Changes", "Deployment Frequency", "Change Failure Rate"], "richtig": 1},
    {"text": "Was versteht man unter ‚Pair Programming‘?", "optionen": ["Zwei Entwickler arbeiten unabhängig an derselben Aufgabe", "Zwei Entwickler teilen sich einen Rechner (einer schreibt Code, der andere reviewt)", "Ein Entwickler programmiert, ein anderer dokumentiert"], "richtig": 1},
    {"text": "Welche der folgenden gilt als Verschwendung im Lean-Sinne in der IT?", "optionen": ["Warten auf Builds", "Code-Reviews", "Automatisierte Tests"], "richtig": 0},
    {"text": "Wozu dienen WIP-Limits (Work in Progress) im Kanban?", "optionen": ["Um die Anzahl der gleichzeitig bearbeiteten Aufgaben zu begrenzen und Engpässe sichtbar zu machen", "Um die Entwicklungsgeschwindigkeit zu reduzieren", "Um die Anzahl der Teammitglieder zu beschränken"], "richtig": 0},
    {"text": "Was ist Kaizen?", "optionen": ["Eine Methode zur Aufwandsschätzung", "Eine Philosophie der kontinuierlichen Verbesserung in kleinen Schritten", "Ein alternatives Framework zu Scrum"], "richtig": 1},
    {"text": "Welche der sieben Verschwendungen bedeutet ‚unnötige Übergabe von Informationen zwischen Teams‘?", "optionen": ["Transport", "Überbearbeitung", "Bewegung"], "richtig": 0},
    {"text": "Was ist die ‚Change Failure Rate‘ (DORA) definiert als?", "optionen": ["Anteil der fehlgeschlagenen Deployments", "Zeit bis zur Wiederherstellung nach einem Ausfall", "Häufigkeit der Auslieferungen"], "richtig": 0},
    {"text": "Welche agile Methode ist bekannt für die Praxis des ‚einfachen Designs‘ (YAGNI)?", "optionen": ["Scrum", "Extreme Programming (XP)", "Kanban"], "richtig": 1},
    {"text": "Was bedeutet die Verschwendung ‚Lagerhaltung‘ in der IT?", "optionen": ["Physische Lagerung von Servern", "Halbfertige Aufgaben und nicht freigegebener Code", "Überfüllte Meetingräume"], "richtig": 1},
    {"text": "Welche DORA-Metrik misst die Zeit von der Idee bis zur Auslieferung in Produktion?", "optionen": ["Deployment Frequency", "Lead Time for Changes", "Time to Restore Service"], "richtig": 1},
    {"text": "Was ist das Ziel des Refaktorisierungsschritts in TDD?", "optionen": ["Den Code zu verschlechtern", "Den Code sauberer und wartbarer zu machen, ohne das Verhalten zu ändern", "Neue Tests zu schreiben"], "richtig": 1},
    {"text": "Welche Aussage über Velocity ist im Vergleich zu DORA-Metriken richtig?", "optionen": ["Velocity misst nur die Geschwindigkeit, nicht die Stabilität", "Velocity ist immer aussagekräftiger als DORA-Metriken", "DORA-Metriken sind ein Ersatz für Velocity"], "richtig": 0},
    {"text": "Was ist das Lean-Prinzip der ‚Just-in-Time‘-Produktion?", "optionen": ["Alles so früh wie möglich produzieren", "Nur das Nötige genau dann produzieren, wenn es benötigt wird", "Große Lagerbestände anlegen"], "richtig": 1},
    {"text": "Welche der sieben Verschwendungen beschreibt ‚Gold Plating‘?", "optionen": ["Überproduktion", "Überbearbeitung", "Fehler"], "richtig": 1},
    {"text": "Was ist ein typisches Werkzeug zur Visualisierung des Arbeitsflusses in Lean?", "optionen": ["Gantt-Diagramm", "Kanban Board", "Netzplan"], "richtig": 1},
    {"text": "Welche DORA-Metrik misst die Zeit, um einen Service nach einem Ausfall wiederherzustellen?", "optionen": ["Time to Restore Service", "Mean Time to Failure", "Change Failure Rate"], "richtig": 0},
    {"text": "Was ist das Ziel von Continuous Integration (CI) in XP?", "optionen": ["Code nur einmal pro Woche zu integrieren", "Code mehrmals täglich in den Hauptzweig zu integrieren und zu testen", "Manuelle Reviews zu ersetzen"], "richtig": 1},
    {"text": "Welche Aussage zur Verschwendung ‚Bewegung‘ ist richtig?", "optionen": ["Physische Bewegung von Teammitgliedern zwischen Räumen", "Häufiger Kontextwechsel und ineffiziente Meetings", "Transport von Code zwischen Abteilungen"], "richtig": 1},
    {"text": "Was ist eine der vier DORA-Metriken?", "optionen": ["Code Coverage", "Deployment Frequency", "Story Points"], "richtig": 1},
    {"text": "Was bedeutet der Lean-Grundsatz ‚Respekt für Menschen‘?", "optionen": ["Mitarbeiter sind austauschbar", "Jeder Mitarbeiter wird in Entscheidungen einbezogen und sein Wissen genutzt", "Nur Führungskräfte treffen Entscheidungen"], "richtig": 1},
    {"text": "Welche der folgenden ist eine XP-Praxis?", "optionen": ["Sprint Planning", "Pair Programming", "Product Backlog"], "richtig": 1},
    {"text": "Was versteht man unter ‚Waste‘ im Lean-Kontext?", "optionen": ["Nicht recycelbare Materialien", "Jede Aktivität, die keinen Mehrwert für den Kunden schafft", "Ungeplante Ausgaben"], "richtig": 1},
    {"text": "Welche DORA-Metrik sollte möglichst niedrig sein?", "optionen": ["Deployment Frequency", "Lead Time for Changes", "Change Failure Rate"], "richtig": 2},
    {"text": "Was ist das Ergebnis des dritten Schritts im TDD-Zyklus (Refaktor)?", "optionen": ["Ein neuer fehlschlagender Test", "Sauberer, wartbarer Code, der alle Tests besteht", "Ein ausgeliefertes Produkt"], "richtig": 1},
    {"text": "Welches Ziel verfolgt die Begrenzung von Work in Progress (WIP) im Kanban?", "optionen": ["Die Anzahl der gleichzeitig bearbeiteten Aufgaben zu reduzieren, um Engpässe zu erkennen und den Durchsatz zu erhöhen", "Die Produktivität zu senken", "Mehr Aufgaben parallel zu bearbeiten"], "richtig": 0},
    {"text": "Was ist die Grundlage für kontinuierliche Verbesserung in Lean?", "optionen": ["Große, einmalige Umstrukturierungen", "Viele kleine, tägliche Verbesserungen (Kaizen)", "Jährliche Qualitätsaudits"], "richtig": 1},
]

# ------------------------------------------------------------
# ZUSAMMENFÜHREN ALLER 11 THEMEN (VOLLSTÄNDIG)
# ------------------------------------------------------------
themen = [
    {"titel": "1. Grundlagen des Projektmanagements", "zusammenfassung": thema1_zusammenfassung, "fragen": thema1_fragen},
    {"titel": "2. Projektziele & Anforderungen", "zusammenfassung": thema2_zusammenfassung, "fragen": thema2_fragen},
    {"titel": "3. Projektstart & Organisation", "zusammenfassung": thema3_zusammenfassung, "fragen": thema3_fragen},
    {"titel": "4. Teamarbeit & Kommunikation", "zusammenfassung": thema4_zusammenfassung, "fragen": thema4_fragen},
    {"titel": "5. Analyse- & Planungswerkzeuge", "zusammenfassung": thema5_zusammenfassung, "fragen": thema5_fragen},
    {"titel": "6. Agiles Projektmanagement (Scrum)", "zusammenfassung": thema6_zusammenfassung, "fragen": thema6_fragen},
    {"titel": "7. Qualitätsmanagement", "zusammenfassung": thema7_zusammenfassung, "fragen": thema7_fragen},
    {"titel": "8. Change Management", "zusammenfassung": thema8_zusammenfassung, "fragen": thema8_fragen},
    {"titel": "9. Projektcontrolling & Berichtswesen", "zusammenfassung": thema9_zusammenfassung, "fragen": thema9_fragen},
    {"titel": "10. Projektvorbereitung & Machbarkeit", "zusammenfassung": thema10_zusammenfassung, "fragen": thema10_fragen},
    {"titel": "11. Lean & agile Methoden (Vertiefung)", "zusammenfassung": thema11_zusammenfassung, "fragen": thema11_fragen},
]

# ------------------------------------------------------------
# GUI-KLASSE (unverändert, aber mit angepasster Listbox-Höhe)
# ------------------------------------------------------------
class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PQSM - Projektmanagement Quiz (Dark Mode)")
        self.root.geometry("1150x850")
        self.root.configure(bg="#2e2e2e")
        self.root.minsize(950, 700)

        self.bg = "#2e2e2e"
        self.fg = "#f0f0f0"
        self.acc_bg = "#1e88e5"

        self.font_title = ("Segoe UI", 18, "bold")
        self.font_header = ("Segoe UI", 13, "bold")
        self.font_text = ("Segoe UI", 12)
        self.font_question = ("Segoe UI", 13)
        self.font_option = ("Segoe UI", 11)

        self.current_thema_idx = 0
        self.quiz_active = False
        self.current_question_index = 0
        self.selected_questions = []
        self.correct_count = 0
        self.total_questions = 0

        # Linker Frame
        self.left_frame = tk.Frame(root, bg="#3a3a3a", width=340)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(root, bg=self.bg)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(self.left_frame, text="📚 Themenauswahl", font=self.font_header,
                 bg="#3a3a3a", fg=self.fg).pack(pady=10)

        # Listbox für 11 Themen (bei Bedarf Scrollbalken)
        self.themen_listbox = tk.Listbox(self.left_frame,
                                         bg="#4a4a4a", fg=self.fg, font=self.font_text,
                                         selectbackground=self.acc_bg, selectforeground="white",
                                         height=16, width=40)
        self.themen_listbox.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        for t in themen:
            self.themen_listbox.insert(tk.END, t["titel"])
        self.themen_listbox.bind("<<ListboxSelect>>", self.on_thema_select)
        self.themen_listbox.selection_set(0)

        self.summary_frame = tk.Frame(self.right_frame, bg=self.bg)
        self.summary_frame.pack(fill=tk.BOTH, expand=True)
        self.question_frame = None

        self.load_thema(0)

    def on_thema_select(self, event):
        if self.quiz_active:
            return
        if not self.themen_listbox.curselection():
            return
        idx = self.themen_listbox.curselection()[0]
        if idx != self.current_thema_idx:
            self.load_thema(idx)

    def load_thema(self, idx):
        self.current_thema_idx = idx
        self.quiz_active = False
        self.themen_listbox.config(state=tk.NORMAL)

        if self.question_frame:
            self.question_frame.destroy()
            self.question_frame = None

        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        self.summary_frame.pack(fill=tk.BOTH, expand=True)

        thema = themen[idx]
        titel = tk.Label(self.summary_frame, text=thema["titel"], font=self.font_title,
                         bg=self.bg, fg=self.fg)
        titel.pack(pady=15)

        text_area = scrolledtext.ScrolledText(self.summary_frame, wrap=tk.WORD,
                                               font=self.font_text, bg="#3a3a3a",
                                               fg=self.fg, relief=tk.FLAT, borderwidth=0,
                                               height=18, padx=15, pady=10)
        text_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        insert_formatted(text_area, thema["zusammenfassung"])

        self.btn_start = tk.Button(self.summary_frame, text="📖 Quiz zu diesem Thema starten",
                                   command=self.start_quiz, font=self.font_header,
                                   bg=self.acc_bg, fg="white", padx=20, pady=10,
                                   relief=tk.FLAT, cursor="hand2")
        self.btn_start.pack(pady=20)

    def start_quiz(self):
        self.quiz_active = True
        self.themen_listbox.config(state=tk.DISABLED)
        self.summary_frame.pack_forget()

        if self.question_frame:
            self.question_frame.destroy()
        self.question_frame = tk.Frame(self.right_frame, bg=self.bg)
        self.question_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        fragen_pool = themen[self.current_thema_idx]["fragen"]
        self.selected_questions = random.sample(fragen_pool, min(10, len(fragen_pool)))
        self.selected_questions = [shuffle_question(q) for q in self.selected_questions]

        self.current_question_index = 0
        self.correct_count = 0
        self.total_questions = len(self.selected_questions)
        self.show_question()

    def show_question(self):
        for widget in self.question_frame.winfo_children():
            widget.destroy()

        if self.current_question_index >= self.total_questions:
            self.finish_topic()
            return

        frage = self.selected_questions[self.current_question_index]

        frage_titel = tk.Label(self.question_frame,
                               text=f"Frage {self.current_question_index+1}/{self.total_questions}",
                               font=self.font_header, bg=self.bg, fg="#bbbbbb")
        frage_titel.pack(pady=(0, 10))

        frage_label = tk.Label(self.question_frame, text=frage["text"],
                               font=self.font_question, bg=self.bg, fg=self.fg,
                               wraplength=800, justify=tk.LEFT)
        frage_label.pack(pady=15)

        self.antwort_var = tk.IntVar(value=-1)
        frame_opts = tk.Frame(self.question_frame, bg=self.bg)
        frame_opts.pack(pady=10)

        for i, opt in enumerate(frage["optionen"]):
            rb = tk.Radiobutton(frame_opts, text=opt, variable=self.antwort_var, value=i,
                                font=self.font_option, bg=self.bg, fg=self.fg,
                                selectcolor=self.bg, activebackground=self.bg,
                                anchor="w", justify=tk.LEFT, padx=15, pady=5)
            rb.pack(anchor="w", pady=5)

        btn_pruefen = tk.Button(self.question_frame, text="Antwort prüfen",
                                command=self.check_answer, font=self.font_header,
                                bg=self.acc_bg, fg="white", padx=25, pady=8,
                                relief=tk.FLAT, cursor="hand2")
        btn_pruefen.pack(pady=20)

        self.feedback_label = tk.Label(self.question_frame, text="", font=self.font_text,
                                       bg=self.bg, fg="#ffaa66")
        self.feedback_label.pack()

    def check_answer(self):
        antwort = self.antwort_var.get()
        if antwort == -1:
            self.feedback_label.config(text="⚠️ Bitte wähle eine Antwort aus!")
            return

        frage = self.selected_questions[self.current_question_index]
        is_correct = (antwort == frage["richtig"])
        if is_correct:
            self.correct_count += 1
            self.feedback_label.config(text="✅ Richtig!", fg="#88ff88")
        else:
            richtiger_text = frage["optionen"][frage["richtig"]]
            self.feedback_label.config(text=f"❌ Leider falsch. Richtig: {richtiger_text}", fg="#ff8888")

        self.root.after(1200, self.next_question)

    def next_question(self):
        self.current_question_index += 1
        self.show_question()

    def finish_topic(self):
        self.quiz_active = False
        if self.question_frame:
            self.question_frame.destroy()
            self.question_frame = None
        self.load_thema(self.current_thema_idx)

        falsch_count = self.total_questions - self.correct_count
        ergebnis_text = f"📊 Ergebnis: {self.correct_count} richtig, {falsch_count} falsch (von {self.total_questions} Fragen)"
        msg = tk.Label(self.summary_frame, text=ergebnis_text,
                       font=self.font_header, bg=self.bg, fg="#88ff88")
        msg.pack(pady=10)
        self.root.after(4000, msg.destroy)

# ------------------------------------------------------------
# Hauptprogramm
# ------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()