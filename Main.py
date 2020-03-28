import requests
import bs4
import pickle
import os
from time import sleep
from tqdm import tqdm
from nltk.corpus import stopwords
from nltk import word_tokenize


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

    # find all tags inside of the body
    body = soup.find_all('div', attrs={'class': 'mw-body-content'})

    # get text from inside of the body. Set to last entry as that seems to be the one with the content
    tags = bs4.BeautifulSoup(body[-1].text, 'html.parser')

    # tokenize words and remove non-alphanumeric elements
    words = list(set([word for word in word_tokenize(tags.text) if word.isalpha()]))

    # remove stopwords
    return [word for word in words if word not in stopwords.words()]


def wiki_crawler(url, save_freq=10, max_requests=100, courtesy_sleep=1):
    """
    This crawler is meant to grab company names from wikipedia. It only goes one level deep for now.

    Args:
        courtesy_sleep: (float): how long to wait between requests
        max_val (int): max number of requests
        save_freq (int): how often to save
        url (str): where to look first
    """
    base_wiki_url = 'https://en.wikipedia.org/'

    # setup vars 
    docs = []

    # get data
    req = requests.get(base_wiki_url + url)

    # parse data
    soup = bs4.BeautifulSoup(req.text, 'html.parser')

    # get body of the text
    body = soup.find_all('div', attrs={'class': 'mw-body-content'})[-1]

    # find all tags
    tags = body.find_all('a', href=True)

    # get the tags with a title
    tags = [tag for tag in tags if tag.has_attr('title')]

    print(f'Crawling from {base_wiki_url + url}...')
    for i, tag in tqdm(enumerate(tags)):
        # get docs from site
        docs += get_docs(base_wiki_url + tag['href'])

        # add courtesy delay so we don't stress their servers too much 
        sleep(courtesy_sleep)

        # save the list every so often so we don't lose everything if we get cut off  
        if i % save_freq == 0 and len(docs) > 0:
            save_pickle(docs, 'data.pickle')

        if (i + 1) % max_requests == 0:
            break

    docs = [d for d in list(set(docs)) if not d.__contains__('list')]

    save_pickle(docs, 'data.pickle')

    return docs


def ngram_dict(docs, bigram_length=2, allow_variable_size=True):
    """
    construct ngrams (bigrams of varying size) and put them into a dictionary. Normalize values.

    Args:
        allow_variable_size (bool): can the bigrams be a variable size?
        bigram_length (int): how long should the ngram be
        docs (object): a list of strings
    """
    # start a dict to keep track of bigrams
    bigram_dict = {}

    # iterate over each doc
    for doc in docs:
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


def get_next_ngram(bigram):
    """ function to return the next bigram """

    ngram_len = len(bigram)

    # find all of the bigrams that start the way our bigram ends, below the randomness threshold
    next_options = {k: v for k, v in ngrams.items() if bigram[1:] == k[:-1]}

    return get_highest_val_ngram(next_options)


def query_dict(max_length=10, start_char='a'):
    """ simple function to generate new texts from a bigram dict

    Args:
        start_char (str): first character to begin with
        max_length (int): how many characters to generate
    """

    # setup text var
    text = start_char

    # get the start bigrams
    start_bigrams = {k: i for k, i in ngrams.items()}

    # get the bigrams that are higher than the random value
    start_ngram = list({k: v for k, v in start_bigrams.items()})
    current_ngram = start_ngram[0]

    # get the first letter
    text += current_ngram[1]

    while len(text) < max_length:
        current_ngram = get_next_ngram(current_ngram)

        # if we find a bigram, then add the value of the next bigram to that
        if current_ngram:
            text += current_ngram[0]
        else:
            break

    return text


if os.path.exists('data.pickle'):
    print('Loading old data.')
    docs = load_pickle('data.pickle')
else:
    print('Crawling...')
    docs = wiki_crawler('wiki/Lists_of_companies', save_freq=1)

ngrams = ngram_dict(docs, 2, allow_variable_size=False)
test = query_dict(max_length=15)
print(test)
