from types import SimpleNamespace

from obstagoon.model.builder import build_model


def test_placeholder_species_move_and_ability_are_excluded_from_model_and_counts():
    project = SimpleNamespace(load_all=lambda: {
        "species_to_national": {
            "SPECIES_NONE": 0,
            "SPECIES_BULBASAUR": 1,
            "SPECIES_EGG": 0,
            "SPECIES_ALCREMIE": 869,
            "SPECIES_ALCREMIE_RUBY_CREAM": 869,
        },
        "form_species_tables": {},
        "species": {
            "SPECIES_NONE": {"speciesName": "None", "graphics": {}, "types": [], "abilities": [], "eggGroups": [], "stats": {}, "evolutions": []},
            "SPECIES_BULBASAUR": {"speciesName": "Bulbasaur", "graphics": {}, "types": [], "abilities": [], "eggGroups": [], "stats": {}, "evolutions": []},
            "SPECIES_EGG": {"speciesName": "Egg", "graphics": {}, "types": [], "abilities": [], "eggGroups": [], "stats": {}, "evolutions": []},
            "SPECIES_ALCREMIE": {"speciesName": "Alcremie", "graphics": {}, "types": [], "abilities": [], "eggGroups": [], "stats": {}, "evolutions": []},
            "SPECIES_ALCREMIE_RUBY_CREAM": {"speciesName": "Alcremie", "graphics": {}, "types": [], "abilities": [], "eggGroups": [], "stats": {}, "evolutions": [], "baseSpecies": "SPECIES_ALCREMIE"},
        },
        "moves": {
            "MOVE_NONE": {"name": "None", "description": "", "type": "TYPE_NORMAL", "power": 0, "accuracy": 0, "pp": 0, "category": "DAMAGE_CATEGORY_STATUS", "flags": []},
            "MOVE_POUND": {"name": "Pound", "description": "", "type": "TYPE_NORMAL", "power": 40, "accuracy": 100, "pp": 35, "category": "DAMAGE_CATEGORY_PHYSICAL", "flags": []},
        },
        "abilities": {
            "ABILITY_NONE": {"name": "None", "description": ""},
            "ABILITY_OVERGROW": {"name": "Overgrow", "description": ""},
        },
        "items": {},
        "types": {},
        "encounters": [],
    })
    model = build_model(project)

    assert "SPECIES_NONE" not in model.species
    assert "SPECIES_EGG" not in model.species
    assert "MOVE_NONE" not in model.moves
    assert "ABILITY_NONE" not in model.abilities
    assert model.metadata["species_count"] == 2
    assert model.metadata["move_count"] == 1
    assert model.metadata["ability_count"] == 1
