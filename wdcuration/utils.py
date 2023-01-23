from itertools import islice


def divide_in_chunks_of_equal_len(arr_range, arr_size):
    """Breaks up a list into a list of lists"""
    return chunk(arr_range, arr_size)


def chunk(arr_range, arr_size):
    """Breaks up a list into a list of lists"""
    arr_range = iter(arr_range)
    return iter(lambda: tuple(islice(arr_range, arr_size)), ())
