import asyncio
from aiohttp import ClientSession
from numpy import dtype
from wdcuration import parse_wikidata_result, render_qs_url
import pandas as pd
import time
from tqdm import tqdm
import inflect
import pandas as pd
from wdcuration import (
    get_wikidata_items_for_id,
    divide_in_chunks_of_equal_len,
)


def print_quickstatements_for_curated_sheet(
    curated_sheet_path, wikidata_property, dropnas=False
):
    qs = get_quickstatements_for_curated_sheet(
        curated_sheet_path, wikidata_property, dropnas=dropnas
    )
    print(render_qs_url(qs))


def get_quickstatements_for_curated_sheet(
    curated_sheet_path, wikidata_property, dropnas=False
):
    """
    Gets a quickstatements from an standardized curation sheet.

    Args:
      curated_sheet_path (str): The path to the sheet of interest.
      wikidata_property (str): The PID of the property to use on Quickstatements.
      dropnas (bool): Whether or not a curation column labeled "ok_row_ was added.
      If true, will dropnas in the column. Useful when good matches are rare.

    """
    df = pd.read_csv(curated_sheet_path, dtype={"id": object})
    if dropnas:
        df = df.dropna(subset=["ok_row"])
    qs = ""
    for i, row in df.iterrows():
        if row["wikidata_id"] != "NONE":
            database_id = row["id"]
            database_p_id = wikidata_property
            wikidata_id = row["wikidata_id"]
            database_label = row["name"]
            qs += f'{wikidata_id}|{database_p_id}|"{database_id}"' + "\n"
            qs += f'{wikidata_id}|Aen|"{database_label}"' + "\n"
    return qs


async def async_search_wikidata(
    search_term,
    session,
    excluded_types=[],
    fixed_type=None,
    exclude_basic=False,
):
    """
    Looks up string on Wikidata.

    Returns a nested dictionary with the search term as key and the associated results as value
    """

    basic_exclusion = list(
        {
            "Q26842193": "journal",
            "Q5633421": "scientific journal",
            "Q737498": "academic journal",
            "Q7725634": "literary work",
            "Q47461344": "written work",
            "Q101352": "family name",
            "Q13442814": "scholarly article",
            "Q732577": "publication",
            "Q3331189": "version, edition or translation",
            "Q187685": "doctoral thesis",
            "Q1266946": "thesis",
            "Q4167410": "disambiguation page",
            "Q16521": "taxon",
            "Q4167836": "Wikimedia category",
            "Q30612": "clinical trial",
            "Q215380": "musical group",
            "Q482994": "musical album",
            "Q105543609": "musical work",
            "Q134556": "music single",
            "Q5": "human",
            "Q838795": "comic strip",
            "Q3305213": "painting",
            "Q21191270": "television series episode",
            "Q15711870": "animated character",
        }.keys()
    )
    excluded_types_local = excluded_types
    # Workaround to avoid accumulation. Not sure why, but they are accumulating.
    excluded_types_local = list(set(excluded_types_local))

    search_expression = search_term
    if exclude_basic:
        for excluded_type in basic_exclusion:
            excluded_types_local.append(excluded_type)  # Disambiguation page

    for excluded_type in excluded_types_local:
        search_expression += f" -haswbstatement:P31={excluded_type} "
    if fixed_type is not None:
        search_expression += f" haswbstatement:P31={fixed_type} "

    base_url = "https://www.wikidata.org/w/api.php?"
    payload = {
        "action": "query",
        "list": "search",
        "srsearch": search_expression,
        "language": "en",
        "format": "json",
        "origin": "*",
    }

    for k, v in payload.items():
        base_url += f"&{k}={v}"

    url = base_url.replace("?&", "?")
    async with session.request("GET", url) as response:

        # Raise if the response code is >= 400.
        # Some 200 codes may still be "ok".
        # You can also pass raise_for_status within
        # client.request().
        response.raise_for_status()

        # Let your code be fully async.  The call to json.loads()
        # is blocking and won't take full advantage.
        #
        # And it does largely the same thing you're doing now:
        # https://github.com/aio-libs/aiohttp/blob/76268e31630bb8615999ec40984706745f7f82d1/aiohttp/client_reqrep.py#L985
        j = await response.json()
        parsed_result = await async_parse_result(j, session)
        return {search_term: parsed_result}


async def async_parse_result(wikidata_result, session):
    base_result = {
        "id": "NONE",
        "label": "NONE",
        "description": "NONE",
        "url": f"https://www.wikidata.org/wiki/NONE",
    }
    # Workaround for when finding no results
    if len(wikidata_result["query"]["search"]) == 0:
        return base_result
    first_item = wikidata_result["query"]["search"][0]
    qid = first_item["title"]
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels|descriptions&ids={qid}&languages=en&format=json"

    async with session.request("GET", url) as response:
        response.raise_for_status()
        data = await response.json()

        label_and_description = {"label": "NONE", "description": "NONE"}

        try:
            label_and_description["label"] = data["entities"][qid]["labels"]["en"][
                "value"
            ]

        except KeyError:
            pass

        try:
            label_and_description["description"] = data["entities"][qid][
                "descriptions"
            ]["en"]["value"]

        except KeyError:
            pass

        return {
            "id": qid,
            "label": label_and_description["label"],
            "description": label_and_description.get("description", "no description"),
            "url": f"https://www.wikidata.org/wiki/{qid}",
        }


async def run_multiple_searches(
    search_terms, fixed_type, excluded_types, exclude_basic=False
):
    tasks = []

    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    async with ClientSession() as session:
        for search_term in search_terms:
            task = asyncio.ensure_future(
                async_search_wikidata(
                    search_term,
                    session,
                    fixed_type=fixed_type,
                    excluded_types=excluded_types,
                    exclude_basic=exclude_basic,
                )
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

    result_dict = {}
    for d in responses:
        result_dict.update(d)
    return result_dict


def generate_curation_spreadsheet(
    identifiers_property,
    curation_table_path,
    output_file_path,
    description_term_lookup="",
    fixed_type=None,
    excluded_types="",
    drop_nones=True,
    exclude_basic=False,
):
    not_on_wikidata = get_subset_not_on_wikidata(
        identifiers_property, curation_table_path, description_term_lookup
    )

    p = inflect.engine()
    search_terms_dict = {}
    search_terms = []
    for i, row in not_on_wikidata.iterrows():

        search_term = p.singular_noun(row["name"])
        if not search_term:
            search_term = row["name"]
        search_terms.append(search_term)
        search_terms_dict[row["name"]] = search_term

    n_per_batch = 25
    list_of_search_lists = list(
        divide_in_chunks_of_equal_len(search_terms, n_per_batch)
    )

    results = {}

    print(f"Running {str(len(search_terms))} searches in batches of {n_per_batch}")
    for group_of_search_terms in tqdm(
        list_of_search_lists, total=len(list(list_of_search_lists))
    ):
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(
            run_multiple_searches(
                group_of_search_terms,
                fixed_type=fixed_type,
                excluded_types=excluded_types,
                exclude_basic=exclude_basic,
            )
        )
        results_now = loop.run_until_complete(future)
        results.update(results_now)
        time.sleep(1)

    not_on_wikidata["search_term"] = not_on_wikidata["name"].map(search_terms_dict)
    not_on_wikidata["wikidata_id"] = not_on_wikidata["search_term"].map(
        {k: v["id"] for k, v in results.items()}
    )
    not_on_wikidata["wikidata_label"] = not_on_wikidata["search_term"].map(
        {k: v["label"] for k, v in results.items()}
    )
    not_on_wikidata["wikidata_description"] = not_on_wikidata["search_term"].map(
        {k: v["description"] for k, v in results.items()}
    )

    if drop_nones:
        not_on_wikidata = not_on_wikidata[not_on_wikidata["wikidata_id"] != "NONE"]
    not_on_wikidata = not_on_wikidata.drop_duplicates()
    not_on_wikidata.to_csv(output_file_path, index=False)


def get_subset_not_on_wikidata(
    identifiers_property, curation_table_path, description_term_lookup
):
    terms_on_wikidata = get_wikidata_items_for_id(identifiers_property)
    full_df = pd.read_csv(
        curation_table_path, on_bad_lines="skip", dtype={"id": object}
    )
    full_df = full_df.dropna(subset=["description"])
    df_subset = full_df.query(
        f"description.str.contains('{description_term_lookup}')",
        engine="python",
    )
    df_subset["id"] = [a.strip() for a in df_subset["id"]]
    not_on_wikidata = df_subset[~df_subset.id.isin(terms_on_wikidata.keys())]
    return not_on_wikidata
