from itertools import islice


def divide_in_chunks_of_equal_len(arr_range, arr_size, return_type="iter"):
    """Breaks up a list into a list of lists"""
    return chunk(arr_range, arr_size, return_type=return_type)


def chunk(arr_range, arr_size, return_type="iter"):
    """Breaks up a list into a list of lists"""
    if return_type == iter:
        arr_range = iter(arr_range)
        return iter(lambda: tuple(islice(arr_range, arr_size)), ())
    else:
        arr_range = iter(arr_range)
        return list(iter(lambda: tuple(islice(arr_range, arr_size)), ()))
