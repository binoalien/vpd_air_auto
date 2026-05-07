# VPD Air Auto V2 — Vollständiger Umsetzungsplan für Codex

## Zweck dieses Dokuments

Dieses Dokument ist die verbindliche technische Arbeitsgrundlage, um `binoalien/vpd_air_auto` von der aktuellen V1-Architektur auf eine V2-Architektur umzubauen. Ziel ist **kein Rewrite von Null**, sondern ein **inkrementelles, testgetriebenes Refactoring** mit klaren Zwischenständen.

Codex soll dieses Dokument als Umsetzungsanweisung verwenden.

---

## Ausgangslage

Die aktuelle Integration ist eine Home-Assistant-Custom-Integration mit einer globalen Konfiguration und einer guten V1-Basis:

- HACS-Integration
- ein einzelner Config Entry (`single_config_entry`)
- globale Optionen für Sensortypen, Namen, Icons und Leaf-Offset
- automatische Device-Discovery über Temperatur- und Feuchtesensoren
- Duplicate Detection für bereits vorhandene Fremdsensoren
- Diagnostics vorhanden
- Testbasis vorhanden
- CI / Ruff / Pylint / Pytest / Hassfest vorhanden

Die V1 ist funktional solide, aber strukturell auf **globale Steuerung** ausgelegt.

Die V2 muss **per device** und **per area** steuerbar werden.

---

## Primäre V2-Ziele

1. Die Integration bleibt **eine** Integration mit **einem** Config Entry.
2. V2 unterstützt Policy-Auflösung auf drei Ebenen:
   - Global Default
   - Area Override
   - Device Override
3. Priorität der Auflösung:
   - Device Override > Area Override > Global Default
4. Die V2-Architektur muss neue Sensorarten und neue Regeln leichter erweiterbar machen.
5. Bestehende Entities sollen nach Möglichkeit stabil bleiben.
6. Bestehende Unique IDs dürfen sich **nicht** ändern.
7. Die Umstellung muss testgetrieben und in kleinen PRs möglich sein.

---

## Bewusste Nicht-Ziele für den ersten V2-Schnitt

Diese Dinge sollen **nicht** im ersten V2-Schnitt umgesetzt werden, außer sie werden später explizit angefordert:

- mehrere Config Entries
- per-device individuelle Icons
- per-device individuelle Namen
- freie Template-Formeln
- neues Entity-ID-Schema
- kompletter Rewrite ohne Rücksicht auf bestehende Tests

---

## Fachlicher Scope von V2.0

V2.0 soll zunächst Folgendes unterstützen:

### Global steuerbar
- Scan-Intervall
- Standardnamen
- Standardicons
- globale Default-Aktivierung pro Sensorart
- globaler Default-Leaf-Offset

### Per Area steuerbar
- Sensorarten aktiv / inaktiv
- Leaf-Offset

### Per Device steuerbar
- Sensorarten aktiv / inaktiv
- Leaf-Offset

### Später vorbereiten, aber nicht zwingend sofort vollständig ausbauen
- manuelle Source Overrides pro Device
  - `temperature_entity_id`
  - `humidity_entity_id`

---

## Aktuelle Kernprobleme in V1

1. `sensor.py` enthält zu viel verteilte Sensortyp-Logik.
2. `coordinator.py` enthält zu viele Verantwortlichkeiten gleichzeitig:
   - Discovery
   - Duplicate Detection
   - Snapshot-Berechnung
   - State-Subscriptions
   - Diagnostics-Zusammenstellung
3. `options.py` ist flach und global gedacht.
4. Sensorarten sind als Strings über mehrere Dateien verstreut.
5. Die Architektur ist nicht auf Area-/Device-Policies vorbereitet.

---

## Zielarchitektur

```text
custom_components/vpd_air_auto/
  __init__.py
  manifest.json
  const.py
  coordinator.py
  diagnostics.py
  sensor.py
  config_flow.py
  migrations.py
  runtime.py

  domain/
    __init__.py
    enums.py
    models.py
    calculations.py
    sensor_definitions.py

  discovery/
    __init__.py
    selection.py
    duplicates.py
    topology.py

  policy/
    __init__.py
    models.py
    repository.py
    resolver.py

  services/
    __init__.py
    snapshot_builder.py
    subscriptions.py
    entity_plan.py
```

Hinweis: `policy/` wird erst nach Phase 2 aktiv eingeführt. Phase 1 und 2 bauen die Tragstruktur.

---

## Architekturprinzipien

1. **Thin HA entrypoints**
   - `__init__.py`, `sensor.py`, `config_flow.py`, `diagnostics.py` bleiben Home-Assistant-Einstiegspunkte, enthalten aber möglichst wenig Businesslogik.

2. **Reine Domainfunktionen**
   - Berechnungen und Heuristiken sollen möglichst pure functions oder kleine Services bleiben.

3. **Deklarative Sensordefinitionen**
   - Sensorarten dürfen nicht in jedem Modul separat per `if/elif` gepflegt werden.

4. **Policy-Auflösung getrennt von Discovery und Snapshot-Building**
   - Discovery findet Topologie.
   - Policy entscheidet, welche Sensortypen aktiv sind und welcher Leaf-Offset gilt.
   - SnapshotBuilder rechnet Werte aus.

5. **Unique-ID-Stabilität**
   - Bereits bestehende Helper-Entities dürfen keine neuen Unique IDs bekommen.

6. **Refactoring in kleinen Schritten**
   - Jede Phase muss in kleinen, reviewbaren Commits / PRs umsetzbar sein.

---

## Ziel-Datenmodell für spätere V2-Policy-Ebene

```python
{
  "scan_interval_seconds": 300,
  "display_policy": {
    "air": {"name": "VPDair", "icon": "mdi:water-opacity"},
    "leaf": {"name": "VPDleaf", "icon": "mdi:leaf"},
    "absolute_humidity": {"name": "Absolute Humidity", "icon": "mdi:water"},
    "dew_point": {"name": "Dew Point", "icon": "mdi:thermometer-water"},
  },
  "global_policy": {
    "enable_air": True,
    "enable_leaf": True,
    "enable_absolute_humidity": True,
    "enable_dew_point": True,
    "leaf_offset_c": -2.0,
  },
  "area_policies": {
    "<area_id>": {
      "enable_leaf": False,
      "leaf_offset_c": -1.0,
    }
  },
  "device_policies": {
    "<device_id>": {
      "enable_air": False,
      "enable_dew_point": True,
      "leaf_offset_c": -2.5,
    }
  },
  "source_overrides": {
    "<device_id>": {
      "temperature_entity_id": "sensor.foo_temp",
      "humidity_entity_id": "sensor.foo_humidity",
    }
  }
}
```

Dieses Modell ist das Ziel, aber **nicht** der Startpunkt der ersten Refactoring-PRs.

---

# Vollständiger Umsetzungsplan nach Phasen

## Phase 0 — Verhalten einfrieren und absichern

### Ziel
Vor jedem strukturellen Umbau muss das aktuelle Verhalten ausreichend durch Tests abgesichert sein.

### Aufgaben
- Bestehende Tests ausführen und grün halten.
- Fehlende Characterization-Tests ergänzen, falls beim Refactoring Lücken sichtbar werden.
- Besonders absichern:
  - `sensor.py`
  - `coordinator.py`
  - `config_flow.py`
  - `options.py`

### Ergebnis
- V1-Verhalten ist sauber eingefroren.
- Refactorings können mit Sicherheitsnetz erfolgen.

---

## Phase 1 — Sensorarten zentralisieren und deklarativ modellieren

### Ziel
Die Sensortyp-Logik aus `sensor.py` herausziehen und in deklarative Definitionen überführen.

### Neue Dateien

#### `domain/enums.py`
Enthält `SensorKind` als `StrEnum`:
- `AIR`
- `LEAF`
- `ABSOLUTE_HUMIDITY`
- `DEW_POINT`

#### `domain/sensor_definitions.py`
Enthält:
- `SensorDefinition` Dataclass
- `SENSOR_DEFINITIONS` Registry
- Getter pro Sensortyp für Snapshot-Felder

Definition pro Sensortyp enthält mindestens:
- `kind`
- `unique_id_suffix`
- `default_name`
- `default_icon`
- `native_unit_of_measurement`
- `device_class`
- `snapshot_value_getter`
- `include_leaf_offset_attribute`

#### `domain/models.py`
Übernimmt `DeviceTopology` und `DeviceSnapshot`.
Bereits jetzt `area_id` und `area_name` ergänzen.

#### `domain/calculations.py`
Die heutige `calculations.py` hierhin verschieben oder spiegeln.

### Bestehende Dateien ändern

#### `sensor.py`
Umbauen auf deklarative Sensordefinitionen.

Statt vieler `if self._kind == ...`-Blöcke:
- `DerivedValueSensor` bekommt `SensorKind`
- lädt `SensorDefinition`
- `native_value`, `available`, `device_class`, `unit` und Leaf-Attribut bauen auf Definitionen auf

Wichtig:
- bestehende Unique-ID-Builder weiterverwenden
- keine Änderung des Unique-ID-Schemas

#### `const.py`
Bleibt zunächst bestehen.
- allgemeine Konstanten behalten
- Unique-ID-Helfer behalten
- SensorKind-String-Konstanten mittelfristig abbauen

### Tests in Phase 1

#### Neue Tests
`tests/test_sensor_definitions.py`

Testen:
- alle Sensorarten haben Definitionen
- Definitionen liefern richtige Units / Device Classes / Snapshot-Mappings
- Leaf-Definition markiert Offset-Attribut korrekt

#### Bestehende Tests anpassen
`tests/test_sensor.py`

Absichern:
- gleiches Außenverhalten wie vorher
- gleiche Unique IDs wie vorher
- gleiche Units, Device Classes und Werte wie vorher

### Akzeptanzkriterien für Phase 1
- Alle bestehenden Sensortests bleiben grün.
- Sensorarten sind zentral über `SensorDefinition` beschrieben.
- `sensor.py` enthält keine groß verteilte Typ-Logik mehr.
- Kein Breaking Change bei bestehenden Entities.

---

## Phase 2 — Coordinator entkernen und Services extrahieren

### Ziel
`coordinator.py` von einem Monolithen zu einem Orchestrator umbauen.

### Neue Dateien

#### `discovery/selection.py`
Die bestehende `selection.py` hierhin verschieben.
Inhalt weitgehend beibehalten.

Verantwortung:
- Kandidaten normalisieren
- beste Quelle für Temperatur / Feuchte auswählen

#### `discovery/duplicates.py`
Neue Serviceklasse `DuplicateDetectionService`.

Verantwortung:
- Fremdsensoren erkennen, die `VPDair`, `VPDleaf`, `Absolute Humidity` oder `Dew Point` faktisch schon liefern
- `blocked_sensor_kinds` liefern

#### `discovery/topology.py`
Neue Serviceklasse `TopologyDiscoveryService`.

Verantwortung:
- Geräte aus Device Registry lesen
- Entities aus Entity Registry lesen
- beste Temperatur-/Feuchtequelle bestimmen
- Area-Zuordnung lesen
- `DeviceTopology` bauen
- Duplicate Detection einbeziehen

#### `services/snapshot_builder.py`
Neue Serviceklasse `SnapshotBuilder`.

Verantwortung:
- aus `DeviceTopology` + aktuellem Leaf-Offset einen `DeviceSnapshot` bauen
- Berechnungen zentral ausführen

#### `services/subscriptions.py`
Neue Serviceklasse `SubscriptionManager`.

Verantwortung:
- nur relevante Source-Entity-IDs abonnieren
- Listener aktualisieren, wenn aktive Contexts wechseln
- Shutdown sauber handhaben

#### `services/entity_plan.py`
Neue Serviceklasse `EntityPlanService`.

Verantwortung:
- berechnen, welche `(device_id, SensorKind)`-Paare als Entities existieren sollen

### Bestehende Dateien ändern

#### `coordinator.py`
Nur noch orchestrieren.

Erlaubte Verantwortlichkeiten nach Phase 2:
- Refresh-Zyklus steuern
- Services verdrahten
- `async_note_context_change()`
- `async_set_updated_data()` aufrufen
- Diagnostics-Payload zusammensetzen

Nicht mehr direkt im Coordinator halten:
- Auswahlheuristik
- Duplicate Heuristik
- Snapshot-Berechnung
- detailliertes Subscription-Management

#### `sensor.py`
`entity_plan()` künftig über Coordinator delegieren, intern aber aus `EntityPlanService` gespeist.

### Tests in Phase 2

Neue Testdateien:
- `tests/test_topology_discovery.py`
- `tests/test_duplicate_detection.py`
- `tests/test_snapshot_builder.py`
- `tests/test_subscriptions.py`

`tests/test_coordinator.py` danach entschlacken:
- nur noch echte Orchestrierungslogik testen
- keine großen fachlichen Heuristiken mehr im Coordinator testen

### Akzeptanzkriterien für Phase 2
- `coordinator.py` ist deutlich kleiner und fokussierter.
- Discovery, Duplicate Detection, Snapshot Building und Subscriptions sind separat testbar.
- Alle bisherigen Funktionen der V1 verhalten sich weiterhin korrekt.

---

## Phase 3 — Policy-Modell und Resolver einführen

### Ziel
Die globale V1-Konfiguration auf eine echte Policy-Architektur vorbereiten.

### Neue Dateien

#### `policy/models.py`
Geplante Modelle:
- `DisplayPolicy`
- `GlobalPolicy`
- `ScopedPolicyOverride`
- `EffectiveDevicePolicy`
- `SourceOverride`

#### `policy/repository.py`
Verantwortung:
- Policy-Daten aus `ConfigEntry` lesen und schreiben
- rohes Entry-Format kapseln

#### `policy/resolver.py`
Verantwortung:
- effektive Policy pro Device auflösen
- Priorität anwenden:
  - Device > Area > Global

### Bestehende Dateien ändern

#### `options.py`
Schrittweise abbauen oder ersetzen.
Der bisherige flache Resolver ist nur V1-tauglich.

#### `coordinator.py`
`SnapshotBuilder` künftig nicht mehr direkt mit `options.leaf_offset_c` aufrufen, sondern mit `EffectiveDevicePolicy.leaf_offset_c`.

#### `sensor.py`
`creatable_kinds_for_device()` später über `EffectiveDevicePolicy` steuern.

### Akzeptanzkriterien für Phase 3
- Policy-Auflösung ist vollständig von Discovery und Snapshot-Berechnung getrennt.
- Es gibt einen klaren Resolver für Device-/Area-/Global-Logik.

---

## Phase 4 — Migration alter V1-Config-Entries

### Ziel
Bestehende Installationen müssen sauber auf V2 überführt werden.

### Neue Datei

#### `migrations.py`
Enthält Migrationshelfer von flachen V1-Einträgen nach V2-Datenstruktur.

### Bestehende Dateien ändern

#### `__init__.py`
`async_migrate_entry()` hinzufügen.

#### `config_flow.py`
Config-Entry-Version erhöhen.

### Migrationslogik
V1-Felder werden wie folgt abgebildet:

- `scan_interval` -> `scan_interval_seconds`
- globale Icons / Namen -> `display_policy`
- `enable_*` -> `global_policy`
- `leaf_offset` -> `global_policy.leaf_offset_c`
- `area_policies`, `device_policies`, `source_overrides` starten leer

### Akzeptanzkriterien für Phase 4
- bestehende Nutzer verlieren keine globale Funktionalität
- bestehende Entities behalten ihre Unique IDs
- V1-Einträge werden automatisch auf V2-Struktur gehoben

---

## Phase 5 — Area-Unterstützung in Discovery und Policy-Auflösung

### Ziel
Area-Kontext in die effektive Device-Konfiguration einbeziehen.

### Änderungen
- `DeviceTopology` nutzt `area_id` / `area_name`
- `PolicyResolver` kann `area_id` auswerten
- `EffectiveDevicePolicy` wird für Geräte mit Area korrekt aus Global + Area berechnet

### Tests
- Device ohne Area nutzt Global Policy
- Device mit Area nutzt Global + Area
- deaktivierte Sensorart auf Area-Level greift korrekt
- Leaf-Offset auf Area-Level überschreibt Global

### Akzeptanzkriterien
- Policies auf Area-Ebene greifen korrekt
- keine Device-Overrides nötig, um Area-Verhalten zu testen

---

## Phase 6 — Device-Unterstützung

### Ziel
Device-Overrides übersteuern Global und Area.

### Änderungen
- `device_policies` aktiv nutzen
- `PolicyResolver` priorisiert Device > Area > Global
- `creatable_kinds_for_device()` basiert auf effektiver Device Policy
- `SnapshotBuilder` bekommt effektiven Leaf-Offset pro Device

### Tests
- Device-Override deaktiviert Sensorart trotz aktiver Area/Global-Policy
- Device-Override überschreibt Leaf-Offset der Area
- Device ohne Override verwendet Area oder Global

### Akzeptanzkriterien
- Prioritätslogik funktioniert deterministisch
- Sensorsichtbarkeit und Leaf-Offset sind pro Device steuerbar

---

## Phase 7 — Config Flow / Options Flow auf scoped Editing umbauen

### Ziel
V2-Policies über die Home-Assistant-UI pflegbar machen.

### Neue UX-Struktur
#### Hauptmenü im Options Flow
- Global Defaults bearbeiten
- Area Override hinzufügen / bearbeiten / löschen
- Device Override hinzufügen / bearbeiten / löschen
- Source Override hinzufügen / bearbeiten / löschen

### Empfehlung für V2.0 UI-Scope
Area- und Device-Overrides zunächst nur für:
- `enable_air`
- `enable_leaf`
- `enable_absolute_humidity`
- `enable_dew_point`
- `leaf_offset_c`

### Vorläufig global belassen
- Namen
- Icons
- Scan-Intervall

### Warum?
So bleibt der erste V2-Flow beherrschbar.

### Tests
- Area Override anlegen
- Area Override aktualisieren
- Area Override löschen
- Device Override anlegen
- Device Override aktualisieren
- Device Override löschen
- Priorität Device > Area > Global indirekt über Options Flow absichern

### Akzeptanzkriterien
- Scoped Policies sind vollständig über den UI-Flow bearbeitbar
- keine YAML-Konfiguration erforderlich

---

## Phase 8 — Source Overrides vorbereiten / optional aktivieren

### Ziel
Manuelle Quellenwahl pro Device möglich machen.

### Änderungen
- `source_overrides` im Policy-/Repository-Layer unterstützen
- `TopologyDiscoveryService` oder ein vorgelagerter Resolver prüft:
  1. manuelles Override vorhanden?
  2. sonst automatische Heuristik

### Tests
- manuell gesetzte Temperaturquelle wird verwendet
- manuell gesetzte Feuchtequelle wird verwendet
- unvollständige oder ungültige Overrides werden abgefangen

### Hinweis
Kann V2.0 oder V2.1 sein. Architektur soll dafür aber früh vorbereitet werden.

---

## Phase 9 — Diagnostics, README, Übersetzungen, Cleanup

### Diagnostics
`diagnostics.py` erweitern um:
- `area_id`
- `area_name`
- `effective_policy`
- `policy_sources` pro Feld
- `source_override_present`
- `blocked_sensor_kinds`
- `entity_plan`

### README
Vollständig aktualisieren:
- neue Policy-Ebenen erklären
- Global / Area / Device Verhalten beschreiben
- Config-Flow-Screens / textuelle Beschreibung ergänzen

### Übersetzungen
`translations/en.json` und `translations/de.json` ergänzen um:
- neue Menüeinträge
- Override-Texte
- Erklärungen zur Vererbung
- Löschen / Zurücksetzen von Overrides

### Cleanup
- alte flache Helper entfernen
- obsolete V1-Testpfade ausdünnen
- interne Imports auf neue Modulstruktur vereinheitlichen

---

# Datei-für-Datei-Arbeitsanweisung

## `__init__.py`
### Kurzfristig
- minimal anpassen, damit neue Services/Runtime eingehängt werden können

### Später
- `async_migrate_entry()` einführen
- Aufbau von Runtime / Repository / Resolver zentralisieren

## `const.py`
### Kurzfristig
- behalten
- Unique-ID-Helfer unverändert lassen

### Später
- sensor-kind-spezifische String-Konstanten abbauen
- nur allgemeine Integrationskonstanten behalten

## `models.py`
### Sofort
- nach `domain/models.py` überführen
- `area_id` / `area_name` ergänzen

## `calculations.py`
### Sofort
- nach `domain/calculations.py` überführen
- Inhalte fachlich nicht verändern

## `selection.py`
### Sofort
- nach `discovery/selection.py` überführen
- Verhalten möglichst nicht verändern

## `sensor.py`
### Sofort
- auf `SensorDefinition` umstellen
- deklarative Registry nutzen
- keine Änderung der Unique IDs

## `coordinator.py`
### Kurzfristig
- schrittweise Services extrahieren
- am Ende nur orchestrieren

## `options.py`
### Noch nicht sofort entfernen
- V1-Flow stabil halten, bis Policy-Layer bereit ist

### Später
- durch `policy/repository.py` + `policy/resolver.py` ersetzen

## `config_flow.py`
### Zunächst stabil halten
- erst nach Phase 4–6 auf scoped Menüführung umbauen

## `diagnostics.py`
### Nach Phase 6/7 ausbauen
- effektive Policy transparent machen

---

# PR-Reihenfolge für Codex

Codex soll den Umbau in **kleinen, reviewbaren PRs** planen. Empfohlene Reihenfolge:

## PR 1
- `domain/enums.py`
- `domain/sensor_definitions.py`
- `tests/test_sensor_definitions.py`

## PR 2
- `sensor.py` auf deklarative Definitionen umstellen
- bestehende Sensor-Tests anpassen

## PR 3
- `discovery/selection.py` extrahieren

## PR 4
- `services/snapshot_builder.py` extrahieren
- Snapshot-bezogene Coordinator-Logik delegieren

## PR 5
- `discovery/duplicates.py` extrahieren

## PR 6
- `discovery/topology.py` extrahieren

## PR 7
- `services/subscriptions.py` extrahieren

## PR 8
- `coordinator.py` auf reine Orchestrierungsrolle reduzieren
- `tests/test_coordinator.py` entschlacken

## PR 9
- `policy/models.py`
- `policy/repository.py`
- `policy/resolver.py`

## PR 10
- Entry-Migration (`async_migrate_entry`)
- V2-Datenstruktur in ConfigEntry integrieren

## PR 11
- Area Policies aktivieren
- Tests ergänzen

## PR 12
- Device Policies aktivieren
- Tests ergänzen

## PR 13
- Config Flow / Options Flow als Menü-Flow umbauen

## PR 14
- optional Source Overrides

## PR 15
- Diagnostics / README / Translations / Cleanup

---

# Teststrategie

## Bestehende Tests beibehalten und schrittweise umbauen
Vorhandene Testdateien:
- `tests/test_calculations.py`
- `tests/test_coordinator.py`
- `tests/test_sensor.py`
- `tests/test_options.py`
- `tests/test_config_flow.py`
- `tests/test_config_flow_direct.py`
- `tests/test_diagnostics.py`
- `tests/test_init.py`

## Neue Tests ergänzen
- `tests/test_sensor_definitions.py`
- `tests/test_topology_discovery.py`
- `tests/test_duplicate_detection.py`
- `tests/test_snapshot_builder.py`
- `tests/test_subscriptions.py`
- später:
  - `tests/test_policy_resolver.py`
  - `tests/test_policy_repository.py`
  - `tests/test_migrations.py`

## Testgrundsätze
1. Neue Services separat testen.
2. Coordinator nur als Orchestrator testen.
3. Keine unnötig fragile Kopplung an private Implementierungsdetails.
4. Unique-ID-Stabilität explizit testen.
5. Policy-Priorität (Device > Area > Global) explizit testen.

---

# Harte technische Regeln für Codex

1. **Keine Änderung des Unique-ID-Schemas**
2. **Keine Big-Bang-PR**
3. **Keine parallele UI- und Architektur-Komplettänderung in einem Schritt**
4. **Immer Ruff, Pylint, Pytest grün halten**
5. **Bestehende Funktionsfähigkeit der V1 während der Refactorings bewahren**
6. **Jede Extraktion zuerst mit Tests absichern, dann Code verschieben**
7. **Public Behavior stabil halten, intern modularisieren**

---

# Definition of Done für V2.0

V2.0 ist erreicht, wenn alle folgenden Punkte erfüllt sind:

- [ ] Sensorarten sind deklarativ modelliert
- [ ] Coordinator ist in Services aufgeteilt
- [ ] V1-Einträge werden nach V2 migriert
- [ ] globale Policies funktionieren weiterhin
- [ ] Area Policies funktionieren
- [ ] Device Policies funktionieren
- [ ] Priorität Device > Area > Global funktioniert nachweislich
- [ ] Config Flow / Options Flow kann Global, Area und Device bearbeiten
- [ ] Diagnostics zeigen effektive Policy nachvollziehbar an
- [ ] Unique IDs bleiben stabil
- [ ] Tests, Ruff, Pylint und CI sind grün
- [ ] README und Übersetzungen sind aktualisiert

---

# Empfohlener Startpunkt für Codex

Codex soll **mit PR 1 beginnen**:

1. `domain/enums.py` anlegen
2. `domain/sensor_definitions.py` anlegen
3. `tests/test_sensor_definitions.py` schreiben
4. noch **keine** Policy-Logik einbauen
5. danach `sensor.py` refactoren

Das ist der risikoärmste und architektonisch sinnvollste Einstieg.

---

# Schlussnotiz

Diese V2 ist **kein kompletter Neuaufbau**, sondern eine kontrollierte Evolution der bestehenden V1. Die aktuelle Integration ist gut genug, dass ein Rewrite unnötig riskant wäre. Der richtige Weg ist ein modularer Umbau in kleinen, testbaren Schritten.

Codex soll sich strikt an diese Reihenfolge halten und keine großen vermischten Architektur-/UI-/Migrationsänderungen in einem einzelnen Schritt durchführen.
