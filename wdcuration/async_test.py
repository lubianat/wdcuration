import asyncio
from aiohttp import ClientSession
from wdcuration import parse_wikidata_result


async def async_search_wikidata(
    search_term,
    session,
    excluded_types=[],
    fixed_type=None,
    exclude_basic=True,
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
            "Q3754629": "taxon",
            "Q4167836": "Wikimedia category",
            "Q30612": "clinical trial",
            "Q215380": "musical group",
            "Q482994": "musical album",
            "Q105543609": "musical work",
            "Q5": "human",
            "Q838795": "comic strip",
        }.keys()
    )
    excluded_types_local = excluded_types

    # Workaround to avoid accumulation. Not sure why, but they are accumulating.
    excluded_types_local = list(set(excluded_types_local))

    search_expression = search_term
    if exclude_basic == True:
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
        return {search_term: j}


async def run_multiple_searches(
    search_terms,
    fixed_type,
    excluded_types,
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
                )
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

    results = {}
    for response_raw in responses:
        for term, response in response_raw.items():
            results[term] = parse_wikidata_result(response)

    return results
