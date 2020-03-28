import pickle
from time import sleep
from tqdm import tqdm
from nltk.corpus import stopwords
from nltk import word_tokenize
import requests
import bs4

""" Crawl wikipedia for data! """


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
        max_requests (int): max number of requests
        save_freq (int): how often to save
        url (str): where to look first
    """
    base_wiki_url = 'https://en.wikipedia.org/'

    # setup vars
    final_docs = []

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
        final_docs += get_docs(base_wiki_url + tag['href'])

        # add courtesy delay so we don't stress their servers too much
        sleep(courtesy_sleep)

        # save the list every so often so we don't lose everything if we get cut off
        if i % save_freq == 0 and len(final_docs) > 0:
            save_pickle(final_docs, 'data.pickle')

        if (i + 1) % max_requests == 0:
            break

    # remove docs that are similar to avoid skewing the data too much
    final_docs = list(set(final_docs))

    save_pickle(final_docs, 'data.pickle')

    return final_docs


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
