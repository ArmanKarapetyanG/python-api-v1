from flask import Flask
from flask_restful import Resource, Api, reqparse
import pandas as pd
import ast
from lxml import etree
import requests
from bs4 import BeautifulSoup
from fake_headers import Headers
from urllib.parse import urlparse
from string import whitespace
import validators

cyrillic_letters = u"0123456789.,"


def stripp(text):
    allowed_chars = cyrillic_letters + whitespace
    return "".join([c for c in text if c in allowed_chars])

app = Flask(__name__)
api = Api(app)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

def parse_it(url):
    parsed_uri = urlparse(url)
    result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return result


def parse_price(url):
    link_status = validators.url(url)
    if link_status:
        data = pd.read_csv('cleanest_max.csv')
        match = data.loc[data['url'].str.contains(url.split('/')[2])].reset_index()
        if len(match) == 1:
            match_xpath = match.loc[0]['xpath']
            if ',' in match_xpath:
                match_xpath = match_xpath.split(',')
            price = None
            nums = 10
            if len(match_xpath) > 2:
                while not price and nums != 0:
                    html_page = requests.get(url, headers=Headers(headers=True).generate()).text
                    soup = BeautifulSoup(html_page, 'lxml')
                    tree = etree.HTML(html_page)
                    price = tree.xpath(match_xpath)
                    nums -= 1
            else:
                while not price and nums != 0:
                    html_page = requests.get(url, headers=Headers(headers=True).generate()).text
                    tree = etree.HTML(html_page)
                    soup = BeautifulSoup(html_page, 'lxml')
                    for i in match_xpath:
                        price = tree.xpath(i)
                    nums -= 1
            if price:
                return stripp(price[0].text.strip())
            else:
                classes = 'ammount, price'.split(',')
                meta_itemprop = 'ammount, price'.split(',')
                id_ = 'ammount, price'.split(',')
                for i in classes:
                    price_span = soup.find('span', class_=i)
                    price_p = soup.find('p', class_=i)
                if price_p:
                    return stripp(price_p.text.strip()).replace(' ', '')
                if price_span:
                    return stripp(price_span.text.strip()).replace(' ', '')
                for i in id_:
                    price_span = soup.find('id', id=i)
                    price_p = soup.find('p', id=i)
                if price_p:
                    return stripp(price_p.text.strip()).replace(' ', '')
                if price_span:
                    return stripp(price_span.text.strip()).replace(' ', '')
                price = soup.find_all('meta')
                for j in price:
                    try:
                        if j['itemprop'] == meta_itemprop[0] or j['itemprop'] == meta_itemprop[1]:
                            p = j['content']
                            if p:
                                return p
                            else:
                                return 0
                    except:
                        return 0
                return 0
        else:
            return None
    else:
        return 'url-error'




class ParseLink(Resource):
    def get(self):
        data = pd.read_csv('cleanest_max.csv')  # read CSV
        data = {'allowed hosts': list(data['host'])}
        return {'data': data}, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', required=True)
        args = parser.parse_args()
        url_to_parse = args['url']
        price = parse_price(url_to_parse)
        print(price)
        if price:
            if price != 'url-error':
                return {'data': {'price': price.replace(' ', '').replace(' ', '')}}, 200
            else:
                return {'data': {'error': 'Wrong url'}}, 400
        else:
            return {'data': {'error': 'Bad Getaway'}}, 500
            
    pass


api.add_resource(ParseLink, '/')

app.run()
