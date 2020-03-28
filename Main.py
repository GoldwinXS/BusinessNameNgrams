import os
from Crawler import wiki_crawler, load_pickle
import numpy as np

""" Construct ngrams and query the dict! """


def ngram_dict(list_of_str, bigram_length=2, allow_variable_size=True):
    """
    construct ngrams (bigrams of varying size) and put them into a dictionary. Normalize values.

    Args:
        allow_variable_size (bool): can the bigrams be a variable size?
        bigram_length (int): how long should the ngram be
        list_of_str (list): a list of strings
    """

    # start a dict to keep track of bigrams
    bigram_dict = {}

    # iterate over each doc
    for doc in list_of_str:
        # iterate over the characters in that doc
        for i in range(len(doc) - bigram_length):

            bigram = tuple(doc[i:i + bigram_length])

            if allow_variable_size:
                # if we've seen this bigram before, then add 1 to the count. Otherwise, add it
                if bigram in bigram_dict:
                    bigram_dict[bigram] += 1
                else:
                    bigram_dict[bigram] = 1
            elif len(bigram) != bigram_length:
                pass
            else:
                if bigram in bigram_dict:
                    bigram_dict[bigram] += 1
                else:
                    bigram_dict[bigram] = 1

    uniques = len(bigram_dict)
    bigrams = {k: v / uniques for k, v in bigram_dict.items()}

    return bigrams


def get_highest_val_ngram(dictionary):
    """
    simply returns the ngram with the highest value

    Args:
        dictionary (dict): a dictionary of ngrams
    """
    max_num = 0
    next_gram = None
    for k, v in dictionary.items():
        if v > max_num:
            max_num = v
            next_gram = k

    return next_gram


def get_next_ngram(bigram, ngram_dict):
    """ function to return the next bigram

    Args:
        bigram (tuple): the ngram from which to look from
        ngram_dict (dict): a dict of bigrams in the form {(str, str , ..., str): float}
    """

    # find all of the bigrams that start the way our bigram ends, below the randomness threshold
    next_options = {k: v for k, v in ngram_dict.items() if bigram[1:] == k[:-1]}

    return get_highest_val_ngram(next_options)


def query_dict(ngram_dict, max_length=10):
    """ simple function to generate new texts from a bigram dict

    Args:
        max_length (int): how many characters to generate
    """

    # # get the start bigrams
    # start_bigrams = {k: i for k, i in ngrams.items()}

    # get the bigrams that are higher than the random value
    # start_ngram = list({k: v for k, v in start_bigrams.items()})
    current_ngram = list(ngram_dict)[np.random.randint(len(ngram_dict))]

    # get the first letter
    text = ''.join(current_ngram)

    while len(text) < max_length:
        current_ngram = get_next_ngram(current_ngram, ngram_dict)

        # if we find a bigram, then add the value of the next bigram to that
        if current_ngram:
            text += current_ngram[-1]
        else:
            break

    return text


# load old data if available, crawl if not
if os.path.exists('data.pickle'):
    print('Loading old data.')
    docs = load_pickle('data.pickle')
else:
    docs = wiki_crawler('wiki/Lists_of_companies', save_freq=1)

# create ngram dict
ngrams = ngram_dict(docs, 5, allow_variable_size=False)

# query the dict and show result
test = query_dict(max_length=15, ngram_dict=ngrams)
print(test)
