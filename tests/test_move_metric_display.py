from obstagoon.model.builder import build_model


class _Project:
    def load_all(self):
        return {
            "species": {},
            "species_to_national": {},
            "form_species_tables": {},
            "moves": {
                "MOVE_COUNTER": {"name": "Counter", "type": "TYPE_FIGHTING", "power": "1", "accuracy": "0", "pp": "20", "category": "DAMAGE_CATEGORY_PHYSICAL", "flags": []},
                "MOVE_SURF": {"name": "Surf", "type": "TYPE_WATER", "power": "90", "accuracy": "100", "pp": "15", "category": "DAMAGE_CATEGORY_SPECIAL", "flags": []},
            },
            "abilities": {},
            "items": {},
            "types": {},
            "encounters": [],
        }


def test_move_metrics_zero_and_one_become_empty_for_templates():
    model = build_model(_Project())
    assert model.moves["MOVE_COUNTER"].power is None
    assert model.moves["MOVE_COUNTER"].accuracy is None
    assert model.moves["MOVE_SURF"].power == "90"
    assert model.moves["MOVE_SURF"].accuracy == "100"
