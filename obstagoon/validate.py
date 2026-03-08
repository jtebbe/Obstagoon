from __future__ import annotations

from pathlib import Path

from .extract.parsers.sprites import validate_graphics


def build_validation_report(project_dir: Path, raw: dict) -> dict:
    species_findings: dict[str, list[dict[str, str]]] = {}
    summary = {
        'species_checked': 0,
        'species_with_findings': 0,
        'errors': 0,
        'warnings': 0,
    }
    for species_id, entry in raw.get('species', {}).items():
        summary['species_checked'] += 1
        findings = validate_graphics(project_dir, species_id, entry.get('graphics', {}))
        if findings:
            species_findings[species_id] = findings
            summary['species_with_findings'] += 1
            for finding in findings:
                if finding.get('severity') == 'error':
                    summary['errors'] += 1
                else:
                    summary['warnings'] += 1
    return {
        'summary': summary,
        'species': species_findings,
    }
