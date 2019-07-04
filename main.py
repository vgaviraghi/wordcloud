# -*- coding: utf-8 -*-

import os
import sqlite3
import string
import time
import nltk
nltk.download('stopwords')
from wordcloud import WordCloud
from bs4 import BeautifulSoup
from tornado import httpclient, gen, queues, web
import wsgiref.handlers
from app import secret_key, static_path
from helpers import encode_string

# Defines the maximum of words to show on Word Cloud
max_words = 100
q_url = queues.Queue()

# Mounts the image path
image_path = os.path.join(*[static_path, 'img', 'wordcloud.jpg'])

# Creates a connection with the database
conn = sqlite3.connect('wordcloud.db')
conn_db = conn.cursor()

# Tries to create a table to save the words and frequencies
try:
    conn_db.execute('''CREATE TABLE top_words (word_name text PRIMARY KEY, word_frequency int)''')
except sqlite3.OperationalError:
    # The table has already been created
    pass

@gen.coroutine
def generate_word_cloud():
    """Generates a WordCloud image with the top 100 words of the page
    """
    # Gets the url informed
    current_url = yield q_url.get()

    # Gets the top 100 words of the page
    page_words = yield get_words_from_url(current_url)

    # Generates a word cloud with the top 100 words
    wordcloud = WordCloud(width=900,height=500, max_words=100,relative_scaling=1,normalize_plurals=False).generate_from_frequencies(page_words)

    # Saves the word cloud in a image to show on browser
    wordcloud.to_file(image_path)

@gen.coroutine
def get_words_from_url(url):
    """Gets the top 100 words of the page
    """
    try:
        # Fetches the website
        response = yield httpclient.AsyncHTTPClient().fetch(url)

        # Gets the body content of the page
        html = response.body if isinstance(response.body, str) \
            else response.body.decode()

        # Parses html page to clean
        soup = BeautifulSoup(html, 'html.parser')

        # Remove all scripts and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Cleans the html and save only the words
        htmlText = soup.get_text(" ")

        # Gets the top 100 words of the page
        words = get_words(htmlText)

    except Exception as e:
        print('Exception: %s %s' % (e, url))
        raise gen.Return([])

    raise gen.Return(words)

def get_words(htmlText):
    """ Return the top 100 words of the page and frequencies
        Only verbs and nouns are considered
    """
    # Gets English stop words
    english_stopwords = nltk.corpus.stopwords.words('english')

    # Gets Pertuguese stop words
    portuguese_stopwords = nltk.corpus.stopwords.words('portuguese')

    # Gets punctuations
    punctuations = list(string.punctuation)

    # Extend some punctuations
    punctuations.extend(['==','q','__','v','s'])

    # Mounts a new list with all stop words
    stopwords = english_stopwords + portuguese_stopwords + punctuations

    # Gets all words in the html
    allWords = nltk.tokenize.word_tokenize(htmlText)

    # Removes all stop words
    allRealWords = [w.lower() for w in allWords if w.lower() not in stopwords]

    # Tags all words
    allWordsTagged = nltk.pos_tag(allRealWords)

    # Separes only nouns and verbs
    allVerbsNouns = [vn[0] for vn in allWordsTagged if vn[1].startswith('NN') or vn[1].startswith('VB')]

    # Gets the frequency of all verbs and nouns of the website
    allWordDist = nltk.FreqDist(w.lower() for w in allVerbsNouns)

    # Mounts a dictionary with all words and frequencies
    wordFrequency = {}
    for word, frequency in allWordDist.most_common(max_words):
        try:
            # Inserts in the database the word (encrypted) and the frequency
            conn_db.execute("insert into top_words values (?, ?)", (encode_string(secret_key, word), frequency))
        except sqlite3.IntegrityError:
            # If the word has already been inserted in the database, update the frequency
            conn_db.execute("update top_words set word_frequency = word_frequency + ? where word_name = ?", (frequency, encode_string(secret_key, word)))

        # Saves the changes in the database
        conn.commit()

        # Saves the word in the dictionary
        wordFrequency[word.encode('utf-8')] = frequency

    # Returns the dictionary of the words
    return wordFrequency

class MainHandler(web.RequestHandler):
    def get(self):

        # Tries to remove olders WordClouds images
        try:
            os.remove(image_path)
        except:
            pass

        # Shows the main page for user inform a URL from some website
        self.render('index.html', wordcloud=None, image_time=None)

    @gen.coroutine
    def post(self):
        # Gets the website url informed by the user
        url_website = self.get_body_argument("url_website")

        # Saves the website url
        q_url.put(url_website)

        # Calls the process to generate a WordCloud
        yield generate_word_cloud()

        # Shows the main page with the WordCloud generated
        self.render("index.html", wordcloud=image_path, image_time=str(int(round(time.time() * 1000))))
