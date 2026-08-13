# Integration of VulnerableCode

## Context

SecObserve is currently reliant on external vulnerability scanners and Google's OSV database for Supply Chain Analysis (SCA). It would be desirable to have an alternative that is

1. running under control of the own organisation and
2. fully Open Source

This is a step towards digital sovereignty by being less dependent on commercial suppliers.

## Considered options

Collecting data directly from sources like NVD, GHSA, RedHat advisories is cumbersome and exactly what VulnerableCode already does.

## Decision

The integration of SecObserve with VulnerableCode consists of:

- Integrated Docker Compose setup including all components of SecObserve and VulnerableCode for development.
- Install instructions for a productive setup for separated instances of SecObserve and VulnerableCode, to be more flexibel, e.g. for separate update schedules.
- SecObserve calls the VulnerableCode API to get vulnerability information for all components of a product / branch having a PURL.
- The integration can be initiated by a user via the UI and API and run as regular background job (analogue to OSV).
- Components are normalised and made first-class citizens, so that every component (identified by its PURL) is unique in the system and references its observations and vulnerabilities directly.
- This changes the imports of CycloneDX and SPDX SBOMs, to use existing components or create new ones on demand.
- Imports from VulnerableCode will then be done incremental, only for components that haven't been scanned for configured amount of time.