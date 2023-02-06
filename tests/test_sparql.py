import unittest
from textwrap import dedent

from wdcuration.sparql import (
    detect_direct_links,
    get_statement_values,
    get_wikidata_items_for_id,
    lookup_id,
    lookup_multiple_ids,
    query_wikidata,
)


class TestWdcurationSPARQL(unittest.TestCase):
    def test_query_wikidata(self):
        basic_query = dedent(
            """
        SELECT ?item ?itemLabel WHERE { ?item wdt:P31 wd:Q146. }
        """
        )

        target = {"item": "http://www.wikidata.org/entity/Q25171691"}
        basic_res = query_wikidata(basic_query)

        self.assertIn(target, basic_res)
        self.assertGreater(len(basic_res), 150)

    def test_get_wikidata_items_for_id(self):
        bioc_packages = get_wikidata_items_for_id("P10892")

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
        result = get_statement_values("Q283350", "P7260")
        self.assertEqual(target, result)

    def test_get_list_with_label(self):
        target = [{"id": "Q8054", "label": "protein"}]
        result = get_statement_values("Q283350", "P31", label=True)
        self.assertEqual(target, result)

    def test_lookup_id(self):
        target = "Q87830400"
        result = lookup_id("10.7554/ELIFE.52614", "P356")

        self.assertEqual(result, target)

    def test_lookup_multiple_ids(self):
        ensg_ids = ["ENSG00000012048", "ENSRNOG00000020701"]
        target = {"ENSG00000012048": "Q227339", "ENSRNOG00000020701": "Q24381608"}

        result = lookup_multiple_ids(ensg_ids, "P594")

        self.assertEqual(result, target)

        target_list = ["Q227339", "Q24381608"]
        result_list = lookup_multiple_ids(ensg_ids, "P594", return_type="list")

        self.assertEqual(result_list, target_list)
