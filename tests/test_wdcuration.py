#!/usr/bin/env python

"""Tests for `wdcuration` package."""


import unittest
import unittest.mock
from textwrap import dedent

import wdcuration as wd


class TestWdcurationSPARQL(unittest.TestCase):
    def test_query_wikidata(self):

        basic_query = dedent(
            """
        SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q146. }
        """
        )

        target = {"item": "http://www.wikidata.org/entity/Q25171691"}
        basic_res = wd.wdcuration.query_wikidata(basic_query)

        self.assertIn(target, basic_res)
        self.assertGreater(len(basic_res), 150)

    def test_get_wikidata_items_for_id(self):

        bioc_packages = wd.wdcuration.get_wikidata_items_for_id("P10892")

        self.assertEqual(bioc_packages["DESeq2"], "Q113018293")

    def test_detect_direct_links(self):
        # TODO: Need basic example
        pass

    def test_lookup_label(self):
        # TODO: Confusing function, unused variables,
        # Should input qid be preceded by 'wd'?
        pass

    def test_get_list(self):
        target = ["1.C.110.1.1"]
        result = wd.wdcuration.get_statement_values("Q283350", "P7260")
        self.assertEqual(target, result)

    def test_get_list_with_label(self):
        target = [{"id": "Q8054", "label": "protein"}]
        result = wd.wdcuration.get_statement_values("Q283350", "P31", label=True)
        self.assertEqual(target, result)

    def test_lookup_id(self):
        target = "Q87830400"
        result = wd.wdcuration.lookup_id("10.7554/ELIFE.52614", "P356")

        self.assertEqual(result, target)

    def test_lookup_multiple_ids(self):

        ensg_ids = ["ENSG00000012048", "ENSRNOG00000020701"]
        target = {"ENSG00000012048": "Q227339", "ENSRNOG00000020701": "Q24381608"}

        result = wd.wdcuration.lookup_multiple_ids(ensg_ids, "P594")

        self.assertEqual(result, target)

        target_list = ["Q227339", "Q24381608"]
        result_list = wd.wdcuration.lookup_multiple_ids(
            ensg_ids, "P594", return_type="list"
        )

        self.assertEqual(result_list, target_list)


class TestWdcurationAPI(unittest.TestCase):
    def test_search_wikidata(self):
        target = {
            "id": "Q155",
            "label": "Brazil",
            "description": "country in South America",
            "url": "https://www.wikidata.org/wiki/Q155",
        }

        result = wd.wdcuration.search_wikidata("brazil")

        self.assertEqual(result, target)

    def test_search_wikidata_fixed(self):
        target = {
            "id": "Q3847505",
            "label": "Federal University of Rio Grande do Norte",
            "description": "federal public university in Natal, Rio Grande do Norte",
            "url": "https://www.wikidata.org/wiki/Q3847505",
        }
        result = wd.wdcuration.search_wikidata("UFRN", fixed_type="Q3918")

        self.assertEqual(result, target)

    def test_get_label_and_description(self):
        target = {"label": "The Blob", "description": "1958 film by Irvin Yeaworth"}
        result = wd.wdcuration.get_label_and_description("Q224964")
        self.assertEqual(target, result)
        result = wd.wdcuration.get_label_and_description("Q224964", method="json_dump")
        self.assertEqual(target, result)
        result = wd.wdcuration.get_label_and_description(
            "Q224964", method="wikidata_api"
        )
        self.assertEqual(target, result)


class TestWdcurationQS(unittest.TestCase):
    def test_convert_date_to_quickstatements(self):
        target = "+2022-01-08T00:00:00Z/11"
        result = wd.wdcuration.convert_date_to_quickstatements("2022-01-08")

        self.assertEqual(result, target)

        target_two = "+2022-12-25T00:00:00Z/11"
        result_monthday = wd.wdcuration.convert_date_to_quickstatements(
            "12/25/2022", format="%m/%d/%Y"
        )

        self.assertEqual(result_monthday, target_two)

    def test_render_quickstatements(self):
        target = 'CREATE\n      \n      LAST|Len|"Item" \n      LAST|Den|"items" \n        LAST|P31|Q5 \n        LAST|P31|Q1650915 \n        LAST|P496|"orcid" '
        example_new_item = wd.wdcuration.NewItemConfig(
            labels={"en": "Item"},
            descriptions={"en": "items"},
            item_property_value_pairs={"P31": ["Q5", "Q1650915"]},
            id_property_value_pairs={"P496": ["orcid"]},
        )
        example_new_item.render_quickstatements()

        self.assertEqual(example_new_item.quickstatements, target)

    @unittest.mock.patch("builtins.input", return_value="y")
    def test_add_key_yes(self, mocked_input):
        target_brazil = {"brazil": "Q155"}
        result = wd.wdcuration.add_key(dictionary={}, string="brazil")
        self.assertEqual(result, target_brazil)

        target_country = {"country": "Q155"}
        result_country = wd.wdcuration.add_key(
            dictionary={}, string="br", dict_key="country", search_string="brazil"
        )
        self.assertEqual(result_country, target_country)

    @unittest.mock.patch("wdcuration.wdcuration.input", create=True)
    def test_add_key_skip(self, mocked_input):
        target = {}
        mocked_input.side_effect = ["n", "skip"]
        result = wd.wdcuration.add_key(dictionary=target, string="brazil")

        self.assertEqual(target, {})

    @unittest.mock.patch("wdcuration.wdcuration.input", create=True)
    def test_add_key_no(self, mocked_input):
        target = {"brazil": "Q25057"}
        mocked_input.side_effect = ["n", "n", "Q25057"]
        result = wd.wdcuration.add_key(dictionary=target, string="brazil")

        self.assertEqual(result, target)

    def test_check_and_save_dict(self):
        # TODO: Need small example
        pass


class TestWdcurationUtils(unittest.TestCase):
    def test_chunk(self):
        target = [(1, 2), (3, 4)]
        result = list(wd.wdcuration.chunk([1, 2, 3, 4], 2))

        self.assertEqual(result, target)
