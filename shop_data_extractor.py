from bs4 import BeautifulSoup
from selenium import webdriver
from utils import * 
from pathlib import Path
import datetime

class Shop():
    def __init__(self, url, opts):
        self.url = url
        self.opts = opts['shop']
        self.source = ""
        self.title = ""
        self.query = ""
        self.csv_text = ""
        self.csv_folder = self.opts['csv_folder']/Path(url_to_folder_name(self.url))

    def get_csv_fname():
        return self.csv_fname

    def get_page(self):
        driver = webdriver.Chrome()
        driver.get(self.url)
        source = driver.page_source
        title = driver.title
        driver.close()
        self.source = source
        self.title = title

    def get_products(self):
        self.get_page()
        self.get_product_text_info()
        self.get_product_attr_info()
        self.save()

    def get_product_text_info(self):
        text_info = self.find_first_n_texts(tag=self.opts['text_tag'], attrs=self.opts['text_attrs'], html_tag_limit=self.opts['html_tag_limit'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+'\nURL: '+self.url+'\n\nPage HTML tag texts:\n[\n'+text_info+']'
        self.csv_text = get_gpt_response(user_message=user_message, system_message=opts['text_system_message'], model=self.opts['model'])

    def get_product_attr_info(self):
        attr_info = self.find_first_n_attrs(tag=self.opts['attr_tag'], search_attrs=self.opts['search_attrs'], result_attrs=self.opts['result_attrs'], html_tag_limit=self.opts['html_tag_limit'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+'\nURL: '+self.url+'\n\nPage HTML tag attributes:\n[\n'+attr_info+']'
        self.csv_attr = get_gpt_response(user_message=user_message, system_message=opts['attr_system_message'], model=self.opts['model'])

    def update_with_attr_info(self):
        attr_info = self.find_first_n_attrs(tag=self.opts['attr_tag'], search_attrs=self.opts['search_attrs'], result_attrs=self.opts['result_attrs'], html_tag_limit=self.opts['html_tag_limit'])
        

    #Use for grabbing html tags with useful text in them that contains things like price, product name, and rating
    #Text can be fed to GPT model for parsing into organized data
    def find_first_n_texts(self, tag, attrs, html_tag_limit=250):
        soup = BeautifulSoup(self.source)
        tag_texts = [t.text.strip().strip('\n') for t in soup.find_all(tag, attrs)]
        tag_texts_nonempty = [t for t in a_tag_texts if t != '']
            return ',\n'.join(tag_texts_nonempty[:html_tag_limit]) if len(tag_texts_nonempty) > html_tag_limit else ',\n'.join(tag_texts_nonempty)

    #Use for grabbing html tags with URLs in them and extracting those URLS
    #Can be fed to GPT model to match Product and Image URLS to their appropriate product entry, so long as enough attributes are given
    def find_first_n_attrs(self, tag, search_attrs, result_attrs, html_tag_limit=250):
        soup = BeautifulSoup(self.source)
        tag_attrs = [{a:t.attrs[a] for a in result_attrs} for t in soup.find_all(tag, search_attrs)]
        return ',\n'.join(tag_attrs[:html_tag_limit]) if len(tag_attrs) > html_tag_limit else ',\n'.join(tag_attrs)

    #Save the CSV string as a csv file, which can then be read into a pandas datafram (easier to combine multiple csvs this way)
    def save(self):
        with open(self.csv_fname) as fout:
            fout.write(self.csv_text)


        

class MetaphorShopSearch():
    def __init__(self, product, pBrand, pStore, metaphor, opts):
        self.shop_opts = opts['shop']
        self.opts = opts['metaphor_shop']
        self.product = product
        self.pBrand = pBrand
        self.pStore = pStore
        self.metaphor = metaphor
        self.system_prompt = self.opts['system_prompt']
        self.query = ""
        self.urls = []
        self.user_q = ""
#        datetime_format = "%Y-%m-%d_%H-%M-%S.txt"

    def build_user_question(self):
        self.user_q = "Product name: "+product+("\nPreferred Brand: "+pBrand if pBrand is not None else "")+("\nPreferred Store: "+pStore if pStore is not None else "")

    #Get the product urls
    def get_urls(self):
        self.query = get_gpt_response(self.user_q, self.system_prompt, self.opts['model'])
        self.current_time = datetime.datetime.now()
        self.current_time_fname = get_timestamp_fname(self.current_time, self.opts['datetime_format'], self.opts['ftype'])
        self.urls = get_metaphor_response(self.query, opts=self.opts)
 
    def extract_shop_data(self, shop):
        shop.get_products()

    def process_shops(self):
        for url in self.urls:
            folder = self.opts['csv_folder']/Path(url_to_folder_name(url))
            if folder.exists() and 



    

    
    

    
