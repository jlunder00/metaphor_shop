from bs4 import BeautifulSoup
from selenium import webdriver
from utils import * 
from pathlib import Path
import datetime
import sys
if sys.version_info[0] < 3: 
    from StringIO import StringIO
else:
    from io import StringIO

import pandas as pd
import streamlit as st

class Shop():
    def __init__(self, url, opts):
        self.url = url
        self.opts = opts
        self.source = ""
        self.title = ""
        self.query = ""
        self.final_df = None
        # self.csv_folder = self.opts['csv_folder']/Path(url_to_folder_name(self.url))
        # do db saving instead later

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
        if self.opts['text_only']:
            csv_text = self.get_product_text_info()
            self.final_df = self.csv_to_df(csv_text)
            return
        if self.opts['attr_only']:
            csv_attr = self.get_product_attr_info()
            self.final_df = self.csv_to_df(csv_attr)
            return

        if self.opts['join_technique'] == 'manual':
            self.final_df
        elif self.opts['join_technique'] == 'update':
            if self.opts['join_source'] == 'text':
                csv_text = self.get_product_text_info()
                csv_combined = self.update_with_attr_info(csv_text)
            else:
                csv_attr = self.get_product_attr_info()
                csv_combined = self.update_with_text_info(csv_attr)
            self.final_df = self.csv_to_df(csv_combined)
        else:
            csv_text = self.get_product_text_info()
            csv_attr = self.get_product_attr_info()
            csv_combined = self.gpt_combine_text_and_attr_info(csv_text, csv_attr)
            self.final_df = self.csv_to_df(csv_combined)



        # self.save() use a DB later to save info between restarts and searches

    def get_product_text_info(self):
        text_info = self.find_first_n_texts(tag=self.opts['text_tag'], attrs=self.opts['text_attrs'], html_tag_limit=self.opts['html_tag_limit'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+'\nURL: '+self.url+'\n\nPage HTML tag texts:\n[\n'+text_info+']'
        return get_gpt_response(user_message=user_message, system_message=opts['text_system_message'], model=self.opts['model'])

    def get_product_attr_info(self):
        attr_info = self.find_first_n_attrs(tag=self.opts['attr_tag'], search_attrs=self.opts['search_attrs'], result_attrs=self.opts['result_attrs'], html_tag_limit=self.opts['html_tag_limit'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+'\nURL: '+self.url+'\n\nPage HTML tag attributes:\n[\n'+attr_info+']'
        return get_gpt_response(user_message=user_message, system_message=opts['attr_system_message'], model=self.opts['model'])

    def update_with_attr_info(self, csv_text):
        attr_info = self.find_first_n_attrs(tag=self.opts['attr_tag'], search_attrs=self.opts['search_attrs'], result_attrs=self.opts['result_attrs'], html_tag_limit=self.opts['html_tag_limit'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+"\nURL: "+self.url+'\n\nExtracted CSV:\n'+csv_text+"\n\nPage HTML tag attributes:\n[\n"+attr_info+"]"
        return get_gpt_response(user_message=user_message, system_message=opts['update_text_with_attr_system_message'], model=self.opts['model'])
    
    def update_with_text_info(self, csv_attr):
        text_info = self.find_first_n_texts(tag=self.opts['attr_tag'], search_attrs=self.opts['search_attrs'], result_attrs=self.opts['result_attrs'], html_tag_limit=self.opts['html_tag_limit'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+"\nURL: "+self.url+'\n\nExtracted CSV:\n'+csv_attr+"\n\nPage HTML tag texts:\n[\n"+text_info+"]"
        return get_gpt_response(user_message=user_message, system_message=opts['update_attr_with_text_system_message'], model=self.opts['model'])

    def gpt_combine_text_and_attr_info(self, csv_text, csv_attr):
        user_message = "Title: "+self.title+'\nQuery: '+self.query+"\nURL: "+self.url+'\n\nExtracted CSV from Texts:\n'+csv_text+"\n\nExtracted CSV from Attributes:\n"+csv_attr
        return get_gpt_response(user_message=user_message, system_message=opts['combine_both_system_message'], model=self.opts['model'])

    def manual_combine_text_and_attr_info(self, csv_text, csv_attr):
        text_df = self.csv_to_df(csv_text)
        attr_df = self.csv_to_df(csv_attr)
        if self.opts['join_source'] == 'text':
            self.final_df = text_df.merge(attr_df, on='Product URL', how='inner')
        else:
            self.final_df = attr_df.merge(text_df, on='Product URL', how='inner')

    def csv_to_df(self, csv):
        return pd.read_csv(StringIO(csv))




        

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


        

class MetaphorShoppingSearch():
    def __init__(self, product, pBrand, pStore, metaphor, opts, shop_opts):
        self.shop_opts = shop_opts
        self.opts = opts
        self.product = product
        self.pBrand = pBrand
        self.pStore = pStore
        self.metaphor = metaphor
        self.system_prompt = self.opts['query_system_prompt']
        self.query = ""
        self.urls = []
        self.shops = []
        self.shop_dfs = []
        self.user_q = ""
#        datetime_format = "%Y-%m-%d_%H-%M-%S.txt"

    def build_user_question(self):
        self.user_q = "Product name: "+self.product+("\nPreferred Brand: "+self.pBrand if self.pBrand is not "" else "")+("\nPreferred Store: "+self.pStore if self.pStore is not "" else "")

    #Get the product urls
    def get_urls(self):
        self.query = get_gpt_response(self.user_q, self.system_prompt, self.opts['model'])

        #get current timestamp to compare to timestamp saved in postgres db that is the last timestamp this url was processed at
        #self.current_time = datetime.datetime.now() work on this later
        # self.current_time_fname = get_timestamp_fname(self.current_time, self.opts['datetime_format'], self.opts['ftype'])
        self.urls = get_metaphor_response(self.metaphor, self.query, opts=self.opts)
 
    def extract_shop_data(self, shop):
        shop.get_products()
        return shop.final_df

    def process_shops(self):
        for url in self.urls:
            # folder = self.opts['csv_folder']/Path(url_to_folder_name(url))
            # if folder.exists() and 
            # Later, use a db to avoid reprocessing urls after restart
            self.shops.append(Shop(url, self.shop_opts))
            self.shop_dfs.append(self.extract_shop_data(shop))



class MetaphorShopping():
    def __init__(self, metaphor, config_path):
        config = load_config(config_path)
        self.opts = opts['metaphor_shop']
        self.search_opts = opts['metaphor_shop_search']
        self.shop_opts = opts['shop']
        self.metaphor = metaphor 
        self.searches = []
        self.searches_data = {'Product':[], 'Brand':[], 'Store':[], 'data':[]}
        # self.searches_data['Product'].append(product)

    def check_existing(self, product, pBrand, pStore):
        for i in range(len(self.searches_data['Product'])):
            if product == self.searches_data['Product'][i] and pBrand == self.searches_data['Brand'] and pStore == self.searches_data['Store']:
                return i
        return -1


    def perform_shop_search(self, product="", pBrand="", pStore=""): 
        idx = self.check_existing(product, pBrand, pStore)
        if idx != -1:
            return self.searches_data['data'][idx]

        self.searches.append(MetaphorShoppingSearch(product, pBrand, pStore, self.metaphor, self.search_opts, self.shop_opts))
        self.searches[-1].build_user_question
        self.searches[-1].get_urls()
        self.searches[-1].extract_shop_data()
        shop_dfs = self.searches[-1].shop_dfs
        if len(shop_dfs) > self.opts['max_urls']:
            shops_to_use = shop_dfs[:self.opts['max_urls']]
        else:
            shops_to_use = shop_dfs
    
        filtered_shop_dfs = [df.head(self.opts['max_products_per_page']) if df.shape[0] > self.opts['max_products_per_page'] else df for df in shops_to_use]

        overall_df = filtered_shop_dfs[0]
        for i in range(1, len(filtered_shop_dfs)):
            overall_df.append(filtered_shop_dfs[i])

        self.searches_data['Product'].append(product)
        self.searches_data['Brand'].append(pBrand)
        self.searches_data['Store'].append(pStore)
        self.searches_data['data'].append(overall_df)
        return self.searches_data['data'][idx]

    def run_search(self, product="", pBrand="", pStore=""):

        data = self.perform_shop_search(product, pBrand, pStore)
        st.write(data)





        





            



    

    
    

    
