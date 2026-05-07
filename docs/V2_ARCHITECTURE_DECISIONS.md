# VPD Air Auto V2 — Architecture Decisions

Dieses Dokument hält die wichtigsten Architekturentscheidungen für die V2 von `vpd_air_auto` fest.

Es dient als leichtgewichtiges ADR-Dokument für:

- Menschen, die die V2 umsetzen oder reviewen
- Codex / andere Coding-Agents
- spätere Nachvollziehbarkeit bei Tradeoffs und Folgeentscheidungen

Es ergänzt:

- `docs/V2_IMPLEMENTATION_PLAN.md`
- `docs/CODEX_V2_PROMPT.md`
- `docs/V2_PR_SERIES_CHECKLIST.md`

---

# ADR 001 — V2 wird ein Refactoring, kein Rewrite

## Status
Accepted

## Kontext
Die bestehende V1 ist keine Wegwerf-Basis. Sie hat bereits:

- funktionierende Home-Assistant-Integration
- Config Flow
- Sensorplattform
- Duplicate Detection
- Diagnostics
- Tests
- CI / Ruff / Pylint / Pytest / Hassfest

Die zentrale Herausforderung ist nicht fehlende Funktionalität, sondern die kommende Unterstützung für:

- per area Steuerung
- per device Steuerung
- spätere optionale Source Overrides

## Entscheidung
V2 wird **kein kompletter Rewrite**.

V2 wird als **inkrementelles, testgetriebenes Refactoring** umgesetzt.

## Begründung
- reduziert Risiko für bestehende Nutzer
- erhält funktionierende V1-Logik
- nutzt vorhandene Tests als Sicherheitsnetz
- erlaubt kleine, reviewbare PRs
- vermeidet unnötigen Entwurfsoverhead

## Konsequenzen
- bestehende Dateien bleiben zunächst als HA-entrypoints erhalten
- interne Logik wird Schritt für Schritt in neue Module extrahiert
- V1-Verhalten bleibt während der Umbauphasen stabil

---

# ADR 002 — Eine Integration, ein Config Entry

## Status
Accepted

## Kontext
Die V2 soll Global / Area / Device unterstützen. Eine mögliche Fehlentscheidung wäre, mehrere Config Entries oder pro Area / pro Device separate Integrationen einzuführen.

## Entscheidung
`vpd_air_auto` bleibt **eine Integration mit einem Config Entry**.

Area- und Device-Konfigurationen werden als **interne Policies** innerhalb dieses Eintrags modelliert.

## Begründung
- fachlich handelt es sich um verschiedene Scopes derselben Integrationslogik
- vermeidet komplexe Mehrfach-Setup- und Migrationspfade
- vereinfacht Diagnostics, Wartung und UX
- passt zur bestehenden `single_config_entry`-Ausrichtung

## Konsequenzen
- V2 braucht ein strukturiertes internes Policy-Modell
- Options Flow muss scoped editing unterstützen
- keine Multi-Entry-Orchestrierung nötig

---

# ADR 003 — Policy-Priorität: Device > Area > Global

## Status
Accepted

## Kontext
Sobald Global-, Area- und Device-Regeln gleichzeitig existieren, muss die Priorität eindeutig und überall identisch sein.

## Entscheidung
Die Auflösung der effektiven Policy erfolgt strikt in dieser Reihenfolge:

1. Device Override
2. Area Override
3. Global Default

## Begründung
- entspricht Nutzererwartung
- ist leicht kommunizierbar
- vermeidet Mehrdeutigkeiten
- lässt sich gut testen und dokumentieren

## Konsequenzen
- `PolicyResolver` wird zentrale Instanz für Prioritätslogik
- Tests müssen die Priorität explizit absichern
- Diagnostics sollen die Quelle eines effektiven Werts sichtbar machen

---

# ADR 004 — Sensorarten werden deklarativ modelliert

## Status
Accepted

## Kontext
In V1 ist die Sensortyp-Logik auf mehrere Stellen verteilt, insbesondere in `sensor.py`.

Änderungen an einer Sensorart betreffen heute mehrere Methoden für:
- Name
- Icon
- Device Class
- Unit
- Value
- Availability
- Extra Attributes

## Entscheidung
Jede Sensorart wird über eine zentrale `SensorDefinition` modelliert.

Zentrale Bausteine:
- `SensorKind`
- `SensorDefinition`
- `SENSOR_DEFINITIONS` Registry

## Begründung
- reduziert verteilte `if/elif`-Logik
- macht neue Sensorarten einfacher
- verbessert Wartbarkeit
- schafft klare Trennung zwischen Sensorbeschreibung und Sensorplattform

## Konsequenzen
- `sensor.py` wird deutlich schlanker
- Sensordetails liegen zentral in `domain/sensor_definitions.py`
- spätere Policy-Anbindung wird einfacher

---

# ADR 005 — Coordinator wird Orchestrator, nicht Fach-Monolith

## Status
Accepted

## Kontext
In V1 bündelt `coordinator.py` viele Verantwortlichkeiten gleichzeitig:
- Topology Discovery
- Duplicate Detection
- Snapshot-Berechnung
- Event-Subscriptions
- Diagnostics-Zusammenstellung
- Delta-Updates

Das skaliert schlecht für V2.

## Entscheidung
Der Coordinator bleibt erhalten, wird aber auf eine **Orchestrator-Rolle** reduziert.

Die eigentliche Fachlogik wird in Services ausgelagert.

## Begründung
- geringere Kopplung
- bessere Testbarkeit
- klarere Verantwortlichkeiten
- erleichtert spätere Policy- und Source-Override-Erweiterungen

## Konsequenzen
Folgende Services werden eingeführt:
- `TopologyDiscoveryService`
- `DuplicateDetectionService`
- `SnapshotBuilder`
- `SubscriptionManager`
- `EntityPlanService`

Der Coordinator:
- verdrahtet
- aktualisiert
- publiziert
- setzt Delta-Updates

---

# ADR 006 — Discovery, Policy und Snapshot-Berechnung werden getrennt

## Status
Accepted

## Kontext
Es wäre naheliegend, Discovery direkt mit Policy-Logik und Snapshot-Rechnung zu vermischen. Das würde aber die Komplexität pro Modul stark erhöhen.

## Entscheidung
Die V2 trennt strikt:

1. **Discovery**
   - Welche Geräte und Quell-Entities existieren?
2. **Policy Resolution**
   - Welche Sensorarten sind für dieses Device effektiv aktiv?
   - Welcher Leaf-Offset gilt effektiv?
3. **Snapshot Building**
   - Welche Werte ergeben sich aus Zuständen + effektiver Policy?

## Begründung
- bessere Verständlichkeit
- einzelne Schritte separat testbar
- weniger Seiteneffekte
- spätere Source Overrides sauber integrierbar

## Konsequenzen
- Discovery kennt noch nicht alle Policy-Details
- SnapshotBuilder bekommt später `EffectiveDevicePolicy`
- Resolver wird eigene zentrale Logikschicht

---

# ADR 007 — Existing Unique IDs bleiben stabil

## Status
Accepted

## Kontext
Ein Wechsel der Unique IDs würde bestehende Entities effektiv neu erzeugen, Historie brechen und Recorder-/Dashboard-/Automation-Nutzung destabilisieren.

## Entscheidung
Die bestehende Unique-ID-Logik bleibt unverändert.

Vorhandene Builder-Funktionen bleiben semantische Referenz.

## Begründung
- schützt Bestandsnutzer
- verhindert unnötige Migrationen
- reduziert Breaking Changes massiv

## Konsequenzen
- Refactorings dürfen interne Architektur ändern, aber nicht das Unique-ID-Schema
- Tests müssen Unique-ID-Stabilität explizit absichern

---

# ADR 008 — Presentation bleibt zunächst global

## Status
Accepted

## Kontext
Mit Area-/Device-Scopes stellt sich die Frage, ob auch Namen und Icons pro Area oder Device überschreibbar sein sollen.

## Entscheidung
In V2.0 bleiben Namen und Icons zunächst **global**.

Scoped Policies (Area / Device) steuern zunächst nur Verhalten:
- Sensorarten aktiv / inaktiv
- Leaf-Offset

## Begründung
- hält den ersten V2-Schnitt kleiner
- reduziert UX- und Übersetzungsaufwand
- vermeidet unnötige Komplexität in Config Flow und Entity-Darstellung
- ermöglicht Fokus auf die fachlich wichtigere Steuerungsebene

## Konsequenzen
- `display_policy` bleibt global
- per-device/per-area Namen und Icons sind frühestens V2.x

---

# ADR 009 — Source Overrides werden vorbereitet, aber nicht erzwungen in V2.0

## Status
Accepted

## Kontext
Manuelle Temperatur- und Feuchtequellen pro Device sind fachlich sinnvoll, aber nicht zwingend notwendig für den ersten V2-Schnitt.

## Entscheidung
Die Architektur wird so vorbereitet, dass Source Overrides später sauber eingebaut werden können.

Sie sind jedoch **nicht automatisch Teil jedes frühen Refactoring-Schritts**.

## Begründung
- vermeidet Scope Creep im Grundumbau
- die wichtigere Basis ist zuerst die Policy- und Service-Architektur
- erlaubt V2.0 ohne vollständige manuelle Source-UX, falls nötig

## Konsequenzen
- Datenmodell soll `source_overrides` bereits vorsehen
- `TopologyDiscoveryService` / Resolver sollen erweiterbar entworfen werden
- vollständige UI-Unterstützung kann PR 14 oder später folgen

---

# ADR 010 — Options Flow wird menübasiert statt flach

## Status
Accepted

## Kontext
Der V1-Options-Flow ist flach und global. Das passt nicht zu Scoped Overrides für Areas und Devices.

## Entscheidung
Der V2-Options-Flow wird schrittweise zu einem **menübasierten Flow** umgebaut.

Geplante Einstiegspunkte:
- Global Defaults bearbeiten
- Area Override hinzufügen / bearbeiten / löschen
- Device Override hinzufügen / bearbeiten / löschen
- später optional Source Overrides

## Begründung
- bessere UX bei komplexeren Einstellungen
- skaliert besser mit Scoped Policies
- vermeidet übergroße Einzel-Formulare

## Konsequenzen
- `config_flow.py` wird erst nach Architektur- und Policy-Basis refactort
- Übersetzungen müssen neue Menü- und Scope-Texte enthalten

---

# ADR 011 — Diagnostics müssen effektive Policies sichtbar machen

## Status
Accepted

## Kontext
Mit mehreren Scopes wird es sonst schwer nachzuvollziehen, warum ein Sensor existiert oder warum ein Leaf-Offset einen bestimmten Wert hat.

## Entscheidung
Diagnostics werden in V2 ausgebaut und sollen mindestens sichtbar machen:
- effektive Policy pro Device
- Quelle eines effektiven Werts (Global / Area / Device)
- `blocked_sensor_kinds`
- Topology
- Snapshot
- später ggf. Source Overrides

## Begründung
- reduziert Support-Aufwand
- verbessert Debugging massiv
- ist bei Scoped Rules praktisch unverzichtbar

## Konsequenzen
- `diagnostics.py` wird nicht nur „mitgezogen“, sondern gezielt erweitert
- Tests sollen Diagnostics-Struktur mitabsichern

---

# ADR 012 — Refactoring-Reihenfolge ist architekturkritisch

## Status
Accepted

## Kontext
Eine falsche Reihenfolge würde unnötige Konflikte erzeugen, etwa wenn UI, Migration und Services gleichzeitig umgebaut werden.

## Entscheidung
Die Reihenfolge der V2-Umsetzung ist verbindlich:

1. Sensorarten deklarativ modellieren
2. Coordinator in Services zerlegen
3. Policy-Modell einführen
4. Migration einführen
5. Area / Device Policies aktivieren
6. Config Flow umbauen
7. optionale Source Overrides
8. Diagnostics / README / Translations / Cleanup

## Begründung
- minimiert Risiko
- schafft stabile Zwischenstände
- vermeidet Big-Bang-Änderungen

## Konsequenzen
- PRs bleiben klein und reviewbar
- spätere Feature-Schritte bauen auf sauberer Tragstruktur auf

---

# ADR 013 — Tests schützen Verhalten, nicht interne Zufälle

## Status
Accepted

## Kontext
Beim Refactoring besteht das Risiko, dass Tests zu stark an private Details gekoppelt sind und dadurch sinnvolle interne Verbesserungen blockieren.

## Entscheidung
Tests sollen schrittweise von zu enger Kopplung auf Verhalten und Modulverantwortung umgestellt werden.

## Begründung
- erlaubt saubere Refactorings
- verbessert Langzeitwartbarkeit der Testbasis
- trennt besser zwischen öffentlichen Invarianten und internen Implementierungsdetails

## Konsequenzen
- neue Service-Tests ergänzen
- `tests/test_coordinator.py` langfristig entschlacken
- Unique IDs, Prioritäten und öffentliche Sensorwerte weiterhin explizit testen

---

# Zusammenfassung der Leitlinien

Für jede V2-Entscheidung gilt:

1. Kein Rewrite, sondern kontrollierte Evolution
2. Eine Integration, ein Config Entry
3. Device > Area > Global
4. Sensorarten deklarativ modellieren
5. Coordinator als Orchestrator
6. Discovery, Policy und Snapshot strikt trennen
7. Unique IDs stabil halten
8. Presentation zunächst global halten
9. Source Overrides vorbereiten, nicht erzwingen
10. Menübasierter Options Flow erst nach der Architekturarbeit
11. Diagnostics als Debugging-Werkzeug ernst nehmen
12. Reihenfolge der Refactorings einhalten
13. Tests auf relevantes Verhalten fokussieren

---

# Nutzungshinweis für Codex

Wenn Codex dieses Dokument liest, gelten folgende Regeln:

- dieses Dokument beschreibt die **architektonischen Leitplanken**
- `docs/V2_IMPLEMENTATION_PLAN.md` beschreibt die **konkrete Umsetzungsreihenfolge**
- `docs/V2_PR_SERIES_CHECKLIST.md` beschreibt die **operative Abarbeitung**
- `docs/CODEX_V2_PROMPT.md` liefert den **Startprompt** für die Arbeit

Bei Zielkonflikten gilt:
1. Unique-ID-Stabilität hat hohe Priorität
2. Kleine, testbare PRs haben Vorrang vor „großen Komplettlösungen“
3. Architekturtrennung hat Vorrang vor kurzfristiger Bequemlichkeit
