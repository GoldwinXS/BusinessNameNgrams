import requests, bs4
import numpy as np
from time import sleep
from tqdm import tqdm
import pickle, os, statistics


def save_pickle(obj, filename):
    """ Simple utility function to save a pickle file

    Args:
        obj: (obj): almost any python object
        filename (str): path where you would like to save the .pickle file. Extension .pickle must be there
    """
    with open(filename, 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_pickle(filename):
    """ Simple utility function to load a pickle file

    Args:
        filename (str): path to the .pickle file in question
    """
    with open(filename, 'rb') as handle:
        return pickle.load(handle)


def get_docs(url):
    """ function which will grab highlighted text from a wikipedia article

    Args:
        url (str): the url string for where to retrieve text
    """

    # set target URL
    target_url = url

    # get data
    req = requests.get(target_url)

    # parse data
    soup = bs4.BeautifulSoup(req.text, 'html.parser')

    # find all tags
    tags = soup.find_all('a')

    # filter tags to the ones that have a "title" attribute. Remove extraneous strings...
    clean = lambda x: x.replace('(page does not exist)', '').replace('(website)', '').replace('(company)',
                                                                                              '').lower() if not x.lower().__contains__(
        'wiki') else None

    # extract text and clean
    tags = [clean(t['title']) for t in tags if t.has_attr('title')]

    # remove any None values
    tags = [t for t in tags if not isinstance(t, type(None))]

    # get out all of the text. Converted to a set to mitigate the affect of extraneous data
    return list(set(tags))


def wiki_crawler(url, save_freq=10, max_val=100, courtesy_sleep=1):
    """

    Args:
        courtesy_sleep: (float): how long to wait between requests
        max_val: (int): max number of requests
        save_freq: (int): how often to save
        url (str): where to look first
    """
    base_wiki_url = 'https://en.wikipedia.org/'

    # setup vars 
    docs = []

    # get data
    req = requests.get(base_wiki_url + url)

    # parse data
    soup = bs4.BeautifulSoup(req.text, 'html.parser')

    # find all tags
    tags = soup.find_all('a', href=True)

    for i, tag in tqdm(enumerate(tags)):
        # get docs from site
        docs += get_docs(base_wiki_url + tag['href'])

        # add courtesy delay so we don't stress their servers too much 
        sleep(courtesy_sleep)

        # save the list every so often so we don't lose everything if we get cut off  
        if i % save_freq == 0 and len(docs) > 0:
            save_pickle(docs, 'data.pickle')

        if i + 1 % max_val == 0:
            break

    docs = list(set(docs))
    docs = [d for d in docs if not d.__contains__('list')]

    save_pickle(docs, 'data.pickle')

    return docs


def make_polygram_dict(docs, bigram_length=2, allow_variable_size=True):
    """
    construct polygrams (bigrams of varying size) and put them into a dictionary. Normalize values.

    Args:
        allow_variable_size: (bool): can the bigrams be a variable size?
        bigram_length: (int): how long should the polygram be
        docs (object): a list of strings
    """
    # start a dict to keep track of bigrams
    bigram_dict = {}

    # iterate over each doc
    for doc in docs:
        # iterate over the characters in that doc
        for i in range(len(doc)):

            # handle the edge cases
            if i == 0:
                bigram = ('START',) + tuple(doc[i:i + bigram_length - 1])
            elif i == len(doc) - bigram_length:
                bigram = tuple(doc[i:i + bigram_length - 1]) + ('STOP',)
            else:
                bigram = tuple(doc[i:i + bigram_length])

            if allow_variable_size:
                # if we've seen this bigram before, then add 1 to the count. Otherwise, add
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

    std = statistics.stdev([x for x in bigram_dict.values()])
    mean = statistics.mean([x for x in bigram_dict.values()])
    normed_bigrams = {k: (v - mean) / std for k, v in bigram_dict.items()}

    return normed_bigrams


def get_next_bigram(bigram, randomness=0.001):
    """ function to return the next bigram """
    len_bigram = len(bigram)

    # find all of the bigrams that start the way our bigram ends, below the randomness threshold
    random_val = np.random.uniform(0, randomness)
    print(bigram[1])
    next_options = {k: v for k, v in normed_bigrams.items() if bigram[1] == k[0]}
    print(next_options)
    max_num = 0
    next_gram = None
    for k, v in next_options.items():
        if v > max_num:
            max_num = v
            next_gram = k

    return next_gram

    #         # pick one out at random and return that. Else return None.
    # if len(next_options) > 0:
    #     random_index = np.random.randint(len(next_options))
    #     return next_options[0]
    # else:
    #     return None


def query_dict(max_length=10, randomness=0.0001):
    """ simple function to generate new texts from a bigram dict

    Args:
        randomness (float): how random the results are. The higher, the more certainty.
        max_length (int): how many characters to generate
    """

    # setup text var
    text = ''

    # get the start bigrams
    start_bigrams = {k: i for k, i in normed_bigrams.items() if k[0] == 'START'}

    # generate a random value
    rand_val = np.random.uniform(0, randomness)

    # get the bigrams that are higher than the random value
    start_bigram = list({k: v for k, v in start_bigrams.items() if v > rand_val})
    current_bigram = start_bigram[np.random.randint(len(start_bigram))]

    # get the first letter
    text += current_bigram[1]

    while len(text) < max_length:
        current_bigram = get_next_bigram(current_bigram, randomness=randomness)

        # if we find a bigram, then add the value of the next bigram to that
        if current_bigram:
            text += current_bigram[0]
        else:
            break

    return text


if os.path.exists('data.pickle'):
    print('Loading old data.')
    docs = load_pickle('data.pickle')
else:
    print('Crawling...')
    docs = wiki_crawler('wiki/Lists_of_companies', save_freq=1)

normed_bigrams = make_polygram_dict(docs, 2, allow_variable_size=False)
test = query_dict(max_length=15,randomness=0.1)
print(test)
