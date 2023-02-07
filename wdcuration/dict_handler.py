"""Dict handling"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from wdcuration.api_searches import add_key, go_to_wikidata, search_wikidata
from wdcuration.quickstatements import render_qs_url


@dataclass
class NewItemConfig:
    """A class containing the information for a new item

    Attributes:
      labels: A dictionary of labels in the format {"langcode": "label"}
      descriptions: A dictionary of descriptions in the format {"langcode": "description"}
      id_property: The property for the target ID for the item, if available.
      id_value:  The value for the target id.
    """

    labels: dict
    descriptions: dict
    item_property_value_pairs: dict = field(default_factory=lambda: {})
    id_property_value_pairs: dict = field(default_factory=lambda: {})
    quickstatements = ""

    def render_quickstatements(self):
        qs = """CREATE
      """
        for k, v in self.labels.items():
            qs += f"""
      LAST|L{k}|"{v}" """

        for k, v in self.descriptions.items():
            qs += f"""
      LAST|D{k}|"{v}" """

        for k, v in self.item_property_value_pairs.items():
            for value in v:
                qs += f"""
        LAST|{k}|{value} """
        for k, v in self.id_property_value_pairs.items():
            for value in v:
                qs += f"""
        LAST|{k}|"{value}" """

        self.quickstatements = qs


@dataclass
class WikidataDictAndKey:
    """
    A class containing the dicts and keys used in reconciliations to Wikidata
    Attributes:
      master_dict: A dict of dicts, each of the inner dicts containing the keys mapped to Wikidata ids.
      dict_name: The name of the inner dict that the new key will be added.
      string: The key and search string to be added to the dict. It is overwritten by
        "dict_key" and "search_string" when available.
      dict_key: The dict key to be added to the curation dictionary.
      search_string: A custom search string, when different from the dict key
      path: The Pathlib path to the folder where the dicts are stored.
      format_function: The function to format the string before the search. Defaults to str (no change).
      excluded_types: A list of Wikidata P31 values to be excluded of the search.

    """

    master_dict: dict
    dict_name: str
    path: Path
    new_item_config: NewItemConfig
    string: str = ""
    dict_key: str = ("",)
    search_string: str = ""
    format_function = str
    excluded_types: List = field(default_factory=lambda: ["Q13442814"])

    def add_key(self, return_qs=False):
        """
        Prompts the user for adding a key to the target dictionary.
        """

        if self.dict_key == "":
            self.dict_key = self.string
        if self.search_string == "":
            self.search_string = self.string

        predicted_id = search_wikidata(self.search_string, self.excluded_types)
        annotated = False

        while annotated == False:
            answer = input(
                f"Is the QID for '{self.search_string}'  \n "
                f"{predicted_id['id']} - {predicted_id['label']} "
                f"({predicted_id['description']}) ? (y/n) "
            )

            if answer == "y":
                self.master_dict[self.dict_name][self.dict_key] = predicted_id["id"]
                annotated = True
            elif answer == "n":
                search = input("Search Wikidata? (y/n/skip/create)")
                if search == "y":
                    go_to_wikidata(self.search_string)
                if search == "n" or search == "y":
                    qid_input = False
                    while qid_input == False:
                        qid = input(
                            f"What is the qid for: '{self.search_string}' ? (QXX/skip/create) "
                        )
                        if "Q" in qid:
                            self.master_dict[self.dict_name][self.dict_key] = qid
                            qid_input = True
                        if qid == "skip":
                            break
                        elif qid == "create":
                            new_item_config = self.new_item_config
                            new_item_config.render_quickstatements()
                            if return_qs:
                                return new_item_config.quickstatements
                            print(new_item_config.quickstatements)
                            print(render_qs_url(new_item_config.quickstatements))

                            break
                    annotated = True
                elif search == "skip":
                    break
                elif search == "create":
                    new_item_config = self.new_item_config
                    new_item_config.render_quickstatements()
                    if return_qs:
                        return new_item_config.quickstatements
                    print(new_item_config.quickstatements)
                    print(render_qs_url(new_item_config.quickstatements))

                    break

            else:
                print("Answer must be either 'y', 'n' ")
            return ""
        if return_qs:
            return ""

    def save_dict(self):
        self.path.joinpath(f"{self.dict_name}.json").write_text(
            json.dumps(self.master_dict[self.dict_name], indent=4, sort_keys=True)
        )


def check_and_save_dict(
    master_dict,
    dict_name,
    string,
    path,
    dict_key="",
    search_string="",
    format_function=str,
    excluded_types: list = ["Q13442814"],
):
    if string not in master_dict[dict_name]:
        master_dict[dict_name] = add_key(
            master_dict[dict_name],
            string,
            dict_key=dict_key,
            search_string=format_function(string),
            excluded_types=excluded_types,
        )
        path.joinpath(f"{dict_name}.json").write_text(
            json.dumps(master_dict[dict_name], indent=4, sort_keys=True)
        )
    return master_dict[dict_name]
