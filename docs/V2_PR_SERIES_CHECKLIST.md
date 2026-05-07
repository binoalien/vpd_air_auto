# VPD Air Auto V2 — PR Series Checklist

Diese Datei dient als praktische Umsetzungs- und Tracking-Checklist für die V2-Migration von `vpd_air_auto`.

Sie ergänzt:

- `docs/V2_IMPLEMENTATION_PLAN.md`
- `docs/CODEX_V2_PROMPT.md`

## Verwendung

- Jede Checkbox entspricht einem sinnvollen PR-Schnitt oder einem klaren Arbeitspaket.
- PRs sollen klein, reviewbar und testbar bleiben.
- Nach jeder PR sollen Ruff, Pylint, Pytest und Hassfest weiterhin grün sein.
- Diese Liste ist absichtlich **inkrementell** aufgebaut. Nicht mehrere große Blöcke gleichzeitig mischen.

---

## Übergeordnete V2-Ziele

- [ ] Deklarative Sensordefinitionen statt verteilter `if/elif`-Logik
- [ ] Entkernter Coordinator mit klaren Services
- [ ] Policy-Modell mit Global / Area / Device
- [ ] Priorität: Device > Area > Global
- [ ] Stable Unique IDs für bestehende Entities
- [ ] UI-Flow für scoped Policies
- [ ] Erweiterte Diagnostics
- [ ] Aktualisierte README- und Übersetzungsdateien

---

# PR-Serie

## PR 1 — Sensorarten zentralisieren

### Ziel
Deklarative Sensordefinitionen einführen, ohne Verhalten der V1 zu brechen.

### Scope
- [ ] `custom_components/vpd_air_auto/domain/enums.py` anlegen
- [ ] `SensorKind` als zentrale Enum einführen
- [ ] `custom_components/vpd_air_auto/domain/sensor_definitions.py` anlegen
- [ ] Deklarative Definitionen für:
  - [ ] `air`
  - [ ] `leaf`
  - [ ] `absolute_humidity`
  - [ ] `dew_point`
- [ ] `tests/test_sensor_definitions.py` anlegen

### Constraints
- [ ] Keine Policy-Logik einführen
- [ ] Keine Unique IDs ändern
- [ ] Kein Config-Flow-Umbau

### Done
- [ ] Neue Domain-Dateien vorhanden
- [ ] Tests für Definitionen vorhanden
- [ ] Bestehendes Verhalten unverändert

---

## PR 2 — `sensor.py` auf deklarative Definitionen umstellen

### Ziel
`sensor.py` auf `SensorDefinition` und `SensorKind` umstellen.

### Scope
- [ ] `sensor.py` auf `SensorKind` umstellen
- [ ] `sensor.py` auf `SensorDefinition` umstellen
- [ ] Verteilte `_kind`-Branching-Logik reduzieren
- [ ] Bestehende Unique-ID-Helfer weiterverwenden
- [ ] `tests/test_sensor.py` anpassen

### Constraints
- [ ] Keine Änderung des Entity-Verhaltens
- [ ] Keine Policy-Resolver-Logik

### Done
- [ ] `sensor.py` ist deutlich schlanker
- [ ] Alle Sensor-Tests grün
- [ ] Unique IDs unverändert

---

## PR 3 — Selection aus dem Coordinator extrahieren

### Ziel
Die heutige Auswahlheuristik auslagern.

### Scope
- [ ] `custom_components/vpd_air_auto/discovery/selection.py` anlegen oder aus alter Datei übernehmen
- [ ] `SourceCandidate` in Discovery-Layer überführen
- [ ] `normalize_identifier()` umziehen
- [ ] `choose_best_entity_id()` umziehen
- [ ] Coordinator-Importe anpassen

### Done
- [ ] Auswahlheuristik lebt nicht mehr im Coordinator-Kontext
- [ ] Tests weiterhin grün

---

## PR 4 — Snapshot Builder extrahieren

### Ziel
Die Snapshot-Berechnung aus dem Coordinator in einen Service ziehen.

### Scope
- [ ] `custom_components/vpd_air_auto/services/snapshot_builder.py` anlegen
- [ ] Berechnung aus `_build_snapshot_for_topology()` dorthin verschieben
- [ ] Coordinator delegiert an `SnapshotBuilder`
- [ ] `tests/test_snapshot_builder.py` anlegen
- [ ] `tests/test_coordinator.py` anpassen

### Done
- [ ] Snapshot-Logik separat testbar
- [ ] Coordinator enthält weniger fachliche Logik

---

## PR 5 — Duplicate Detection extrahieren

### Ziel
Duplicate-Erkennung als eigenen Service auslagern.

### Scope
- [ ] `custom_components/vpd_air_auto/discovery/duplicates.py` anlegen
- [ ] Alias-Logik aus Coordinator übertragen
- [ ] Erkennung bestehender Fremd-Sensoren in Service verschieben
- [ ] `tests/test_duplicate_detection.py` anlegen
- [ ] Coordinator delegiert Duplicate Detection

### Done
- [ ] `blocked_sensor_kinds` werden extern berechnet
- [ ] Duplicate Detection separat testbar

---

## PR 6 — Topology Discovery extrahieren

### Ziel
Discovery von Device Registry / Entity Registry in eigenen Service ziehen.

### Scope
- [ ] `custom_components/vpd_air_auto/discovery/topology.py` anlegen
- [ ] Temperatur-/Feuchtequellen pro Gerät im Service bestimmen
- [ ] `area_id` / `area_name` vorbereiten
- [ ] Coordinator delegiert Discovery
- [ ] `tests/test_topology_discovery.py` anlegen

### Done
- [ ] Coordinator macht keine vollständige Discovery mehr selbst
- [ ] Topology Discovery separat testbar

---

## PR 7 — Subscription Management extrahieren

### Ziel
State-Change-Listener von der Coordinator-Klasse trennen.

### Scope
- [ ] `custom_components/vpd_air_auto/services/subscriptions.py` anlegen
- [ ] Listener-Aufbau / Austausch / Shutdown auslagern
- [ ] Coordinator delegiert an `SubscriptionManager`
- [ ] `tests/test_subscriptions.py` anlegen

### Done
- [ ] Subscriptions separat testbar
- [ ] Coordinator wird weiter entlastet

---

## PR 8 — Coordinator auf Orchestrator-Rolle reduzieren

### Ziel
`coordinator.py` auf saubere Orchestrierung beschränken.

### Scope
- [ ] Coordinator nutzt:
  - [ ] `TopologyDiscoveryService`
  - [ ] `DuplicateDetectionService`
  - [ ] `SnapshotBuilder`
  - [ ] `SubscriptionManager`
  - [ ] `EntityPlanService`
- [ ] `EntityPlanService` anlegen
- [ ] `tests/test_coordinator.py` entschlacken

### Done
- [ ] Coordinator ist deutlich kleiner
- [ ] Fachlogik liegt primär in Services

---

## PR 9 — Policy-Modelle einführen

### Ziel
Basis für Global / Area / Device Policies schaffen.

### Scope
- [ ] `custom_components/vpd_air_auto/policy/models.py` anlegen
- [ ] Modelle definieren:
  - [ ] `DisplayPolicy`
  - [ ] `GlobalPolicy`
  - [ ] `ScopedPolicyOverride`
  - [ ] `EffectiveDevicePolicy`
  - [ ] `SourceOverride`
- [ ] `custom_components/vpd_air_auto/policy/repository.py` anlegen
- [ ] `custom_components/vpd_air_auto/policy/resolver.py` anlegen
- [ ] `tests/test_policy_repository.py` anlegen
- [ ] `tests/test_policy_resolver.py` anlegen

### Done
- [ ] Policy-Ebene existiert unabhängig von Discovery und Sensorplattform

---

## PR 10 — V1 → V2 Entry-Migration

### Ziel
Bestehende Installationen in die neue Datenstruktur überführen.

### Scope
- [ ] `custom_components/vpd_air_auto/migrations.py` anlegen
- [ ] `async_migrate_entry()` einführen
- [ ] V1-Felder auf V2-Struktur mappen
- [ ] `tests/test_migrations.py` anlegen
- [ ] `tests/test_init.py` anpassen

### Constraints
- [ ] Keine Unique IDs ändern
- [ ] Bestehende globale Konfiguration muss erhalten bleiben

### Done
- [ ] V1-Entry wird transparent nach V2 migriert

---

## PR 11 — Area Policies aktivieren

### Ziel
Area-Ebene produktiv nutzen.

### Scope
- [ ] `TopologyDiscoveryService` liefert Area-Kontext zuverlässig
- [ ] `PolicyResolver` wendet `area_policies` an
- [ ] `creatable_kinds_for_device()` berücksichtigt Area-Overrides
- [ ] Leaf-Offset kann aus Area-Policy kommen
- [ ] Tests für Area-Priorität ergänzen

### Done
- [ ] Geräte innerhalb einer Area nutzen Area-Overrides korrekt

---

## PR 12 — Device Policies aktivieren

### Ziel
Device-Ebene als höchste Priorität aktivieren.

### Scope
- [ ] `PolicyResolver` wendet `device_policies` an
- [ ] Device-Overrides übersteuern Area / Global
- [ ] `SnapshotBuilder` nutzt effektive Device-Policy
- [ ] Tests für Device > Area > Global ergänzen

### Done
- [ ] Device-Priorität funktioniert deterministisch

---

## PR 13 — Config Flow / Options Flow auf Scoped Editing umbauen

### Ziel
V2-Policies über die UI pflegbar machen.

### Scope
- [ ] Menü-basierter Options Flow
- [ ] Global Defaults bearbeiten
- [ ] Area Override hinzufügen / bearbeiten / löschen
- [ ] Device Override hinzufügen / bearbeiten / löschen
- [ ] Vorläufig nur Behavior-Felder auf Scoped-Ebene:
  - [ ] `enable_air`
  - [ ] `enable_leaf`
  - [ ] `enable_absolute_humidity`
  - [ ] `enable_dew_point`
  - [ ] `leaf_offset_c`
- [ ] `tests/test_config_flow.py` erweitern

### Done
- [ ] Policies sind vollständig über UI verwaltbar

---

## PR 14 — Optionale Source Overrides

### Ziel
Manuelle Temperatur-/Feuchtequelle pro Device ermöglichen.

### Scope
- [ ] `source_overrides` im Repository speichern
- [ ] Resolver / Discovery berücksichtigen manuelle Source Overrides
- [ ] Validierung für manuelle Quellen ergänzen
- [ ] Tests für manuelle Source-Bindings ergänzen

### Done
- [ ] Manuelle Quellenwahl funktioniert ohne globale Heuristik zu zerstören

---

## PR 15 — Diagnostics, README, Übersetzungen, Cleanup

### Ziel
V2 finalisieren und dokumentieren.

### Scope
- [ ] `diagnostics.py` erweitern um:
  - [ ] effektive Policy
  - [ ] Policy-Quelle je Feld
  - [ ] Area-Information
  - [ ] `blocked_sensor_kinds`
  - [ ] `entity_plan`
- [ ] `README.md` vollständig aktualisieren
- [ ] `translations/en.json` erweitern
- [ ] `translations/de.json` erweitern
- [ ] alte V1-Helfer entfernen, wenn obsolet
- [ ] Changelog ergänzen

### Done
- [ ] V2 ist dokumentiert, übersetzt und diagnostizierbar

---

# Querschnitts-Checklist für jede PR

Diese Punkte gelten **für jede PR**:

- [ ] Scope klein und reviewbar
- [ ] Keine unnötigen Nebenschauplätze gemischt
- [ ] Ruff grün
- [ ] Pylint grün
- [ ] Pytest grün
- [ ] Hassfest nicht beschädigt
- [ ] Keine Änderung bestehender Unique IDs
- [ ] Öffentliche V1-Funktionalität bleibt stabil, sofern nicht explizit geplant
- [ ] Neue Architekturdateien sind klar dokumentiert und typisiert

---

# Definition of Done für die gesamte V2-Serie

- [ ] Sensorarten sind deklarativ modelliert
- [ ] Coordinator ist in Services zerlegt
- [ ] V1-Entry-Migration existiert
- [ ] Global / Area / Device Policies funktionieren
- [ ] Priorität Device > Area > Global ist testbar abgesichert
- [ ] Scoped Options Flow ist verfügbar
- [ ] Diagnostics sind deutlich verbessert
- [ ] README ist aktuell
- [ ] Übersetzungen sind aktuell
- [ ] CI / Ruff / Pylint / Pytest / Hassfest grün

---

# Empfehlung für den Start

Der beste Einstieg ist **PR 1**.

Nicht mit Policies oder Config Flow anfangen.
Zuerst die Sensorarten und ihre Definitionen sauber zentralisieren.
