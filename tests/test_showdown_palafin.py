from pathlib import Path
from types import SimpleNamespace

from obstagoon.generate.showdown import ShowdownExportGenerator
from obstagoon.model.schema import LearnsetBucket, ObstagoonModel, SpeciesRecord


def make_config(tmp_path: Path):
    canonical = tmp_path / 'pokedex.ts'
    canonical.write_text('''export const Pokedex = {\n\tpalafin: {\n\t\tnum: 964,\n\t\tname: "Palafin",\n\t\totherFormes: ["Palafin-Hero"],\n\t\tformeOrder: ["Palafin", "Palafin-Hero"]\n\t},\n\tpalafinhero: {\n\t\tnum: 964,\n\t\tname: "Palafin-Hero",\n\t\tbaseSpecies: "Palafin",\n\t\tforme: "Hero"\n\t},\n};\n''', encoding='utf-8')
    return SimpleNamespace(
        showdown_export_dir=tmp_path / 'showdown-export',
        dist_dir=tmp_path / 'dist' / 'site',
        verbose=False,
        showdown_canonical_pokedex_path=canonical,
    )


def test_palafin_hero_uses_showdown_style_name(tmp_path: Path):
    model = ObstagoonModel(
        species={
            'SPECIES_PALAFIN': SpeciesRecord(
                species_id='SPECIES_PALAFIN',
                national_dex=964,
                name='Palafin',
                types=['Water'],
                abilities=['Zero to Hero'],
                egg_groups=['Field', 'Water 2'],
                stats={'Base HP': '100', 'Base Attack': '70', 'Base Defense': '72', 'Base Sp. Attack': '53', 'Base Sp. Defense': '62', 'Base Speed': '100', 'Height': '13', 'Weight': '602'},
                category='Dolphin',
                learnsets=LearnsetBucket(),
                form_changes=[{'method': 'FORM_CHANGE_BATTLE_SWITCH', 'target_species': 'SPECIES_PALAFIN_HERO', 'item': None}],
            ),
            'SPECIES_PALAFIN_HERO': SpeciesRecord(
                species_id='SPECIES_PALAFIN_HERO',
                national_dex=964,
                name='Palafin-Palafin Hero',
                base_species='SPECIES_PALAFIN',
                form_name='Palafin Hero',
                form_index=1,
                types=['Water'],
                abilities=['Zero to Hero'],
                egg_groups=['Field', 'Water 2'],
                stats={'Base HP': '100', 'Base Attack': '160', 'Base Defense': '97', 'Base Sp. Attack': '106', 'Base Sp. Defense': '87', 'Base Speed': '100', 'Height': '18', 'Weight': '974'},
                category='Hero',
                learnsets=LearnsetBucket(),
            ),
        },
        moves={},
        abilities={},
        items={},
        types={},
        encounters=[],
        sprites=[],
        species_to_national={},
        national_to_species={},
        forms={},
        metadata={},
    )
    gen = ShowdownExportGenerator(make_config(tmp_path), model)
    gen._build_species_entries()
    assert 'palafinhero' in gen._species_entries
    hero = gen._species_entries['palafinhero']
    assert hero.display_name == 'Palafin-Hero'
    pokedex = gen._render_pokedex_ts()
    assert 'palafinhero: {' in pokedex
    assert 'name: "Palafin-Hero"' in pokedex
    assert 'otherFormes: ["Palafin-Hero"]' in pokedex
    assert 'formeOrder: ["Palafin", "Palafin-Hero"]' in pokedex
    assert 'requiredAbility: "Zero to Hero"' in pokedex
    assert 'battleOnly: "Palafin"' in pokedex
