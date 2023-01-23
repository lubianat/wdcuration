import unittest
import unittest.mock

from wdcuration.api_searches import add_key, get_label_and_description, search_wikidata


class TestWdcurationAPI(unittest.TestCase):
    def test_search_wikidata(self):
        target = {
            "id": "Q155",
            "label": "Brazil",
            "description": "country in South America",
            "url": "https://www.wikidata.org/wiki/Q155",
        }

        result = search_wikidata("brazil")

        self.assertEqual(result, target)

    def test_search_wikidata_fixed(self):
        target = {
            "id": "Q3847505",
            "label": "Federal University of Rio Grande do Norte",
            "description": "federal public university in Natal, Rio Grande do Norte",
            "url": "https://www.wikidata.org/wiki/Q3847505",
        }
        result = search_wikidata("UFRN", fixed_type="Q3918")

        self.assertEqual(result, target)

    def test_get_label_and_description(self):
        target = {"label": "The Blob", "description": "1958 film by Irvin Yeaworth"}
        result = get_label_and_description("Q224964")
        self.assertEqual(target, result)
        result = get_label_and_description("Q224964", method="json_dump")
        self.assertEqual(target, result)
        result = get_label_and_description("Q224964", method="wikidata_api")
        self.assertEqual(target, result)

    @unittest.mock.patch("builtins.input", return_value="y")
    def test_add_key_yes(self, mocked_input):
        target_brazil = {"brazil": "Q155"}
        result = add_key(dictionary={}, string="brazil")
        self.assertEqual(result, target_brazil)

        target_country = {"country": "Q155"}
        result_country = add_key(
            dictionary={}, string="br", dict_key="country", search_string="brazil"
        )
        self.assertEqual(result_country, target_country)

    @unittest.mock.patch("wdcuration.api_searches.input", create=True)
    def test_add_key_skip(self, mocked_input):
        target = {}
        mocked_input.side_effect = ["n", "skip"]
        result = add_key(dictionary=target, string="brazil")

        self.assertEqual(target, {})

    @unittest.mock.patch("wdcuration.api_searches.input", create=True)
    def test_add_key_no(self, mocked_input):
        target = {"brazil": "Q25057"}
        mocked_input.side_effect = ["n", "n", "Q25057"]
        result = add_key(dictionary=target, string="brazil")

        self.assertEqual(result, target)
