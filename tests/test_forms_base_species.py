from types import SimpleNamespace

from obstagoon.model.builder import build_model


def test_forms_derived_from_base_species_without_form_table():
    project = SimpleNamespace(load_all=lambda: {
        "species_to_national": {"SPECIES_ALCREMIE": 869, "SPECIES_ALCREMIE_RUBY_CREAM": 869},
        "form_species_tables": {},
        "species": {
            "SPECIES_ALCREMIE": {"speciesName": "Alcremie", "graphics": {}, "types": [], "abilities": [], "eggGroups": [], "stats": {}, "evolutions": []},
            "SPECIES_ALCREMIE_RUBY_CREAM": {"speciesName": "Alcremie", "graphics": {}, "types": [], "abilities": [], "eggGroups": [], "stats": {}, "evolutions": [], "baseSpecies": "SPECIES_ALCREMIE"},
        },
        "moves": {}, "abilities": {}, "items": {}, "types": {}, "encounters": []
    })
    model = build_model(project)
    assert "SPECIES_ALCREMIE_RUBY_CREAM" in model.species["SPECIES_ALCREMIE"].forms
    assert model.species["SPECIES_ALCREMIE_RUBY_CREAM"].base_species == "SPECIES_ALCREMIE"
