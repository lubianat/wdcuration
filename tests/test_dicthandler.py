import unittest

from wdcuration.dict_handler import NewItemConfig, check_and_save_dict


class TestWdcurationDictHandler(unittest.TestCase):
    def test_render_quickstatements(self):
        target = 'CREATE\n      \n      LAST|Len|"Item" \n      LAST|Den|"items" \n        LAST|P31|Q5 \n        LAST|P31|Q1650915 \n        LAST|P496|"orcid" '
        example_new_item = NewItemConfig(
            labels={"en": "Item"},
            descriptions={"en": "items"},
            item_property_value_pairs={"P31": ["Q5", "Q1650915"]},
            id_property_value_pairs={"P496": ["orcid"]},
        )
        example_new_item.render_quickstatements()

        self.assertEqual(example_new_item.quickstatements, target)

    def test_check_and_save_dict(self):
        # TODO: Need small example
        pass
