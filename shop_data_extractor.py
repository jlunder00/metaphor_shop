from bs4 import BeautifulSoup
from selenium import webdriver
from utils import * 
from pathlib import Path
import datetime
import sys
from urllib.parse import urlparse
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
        self.url_parsed = urlparse(self.url)
        self.url_root = self.url_parsed.scheme+'://'+self.url_parsed.netloc
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
            self.no_product_urls_df = self.csv_to_df(csv_text)
            return
        if self.opts['attr_only']:
            csv_attr = self.get_product_attr_info()
            self.no_product_urls_df = self.csv_to_df(csv_attr)
            return

        if self.opts['join_technique'] == 'manual':
            csv_attr = self.get_product_attr_info()
            csv_text = self.get_product_text_info()
            self.no_product_urls_df = self.manual_combine_text_and_attr_info(csv_text, csv_attr)
        elif self.opts['join_technique'] == 'update':
            if self.opts['join_source'] == 'text':
                csv_text = self.get_product_text_info()
                csv_combined = self.update_with_attr_info(csv_text)
            else:
                csv_attr = self.get_product_attr_info()
                csv_combined = self.update_with_text_info(csv_attr)
            self.no_product_urls_df = self.csv_to_df(csv_combined)
        else:
            csv_text = self.get_product_text_info()
            csv_attr = self.get_product_attr_info()
            csv_combined = self.gpt_combine_text_and_attr_info(csv_text, csv_attr)
            self.no_product_urls_df = self.csv_to_df(csv_combined)

        self.find_product_urls()



        # self.save() use a DB later to save info between restarts and searches

    def get_product_text_info(self):
        text_info = self.find_first_n_texts(tag=self.opts['text_tag'], attrs=self.opts['text_attrs'], html_tag_min=self.opts['html_tag_min']['text'], html_tag_limit=self.opts['html_tag_limit']['text'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+'\nURL: '+self.url+'\n\nPage HTML tag texts:\n[\n'+text_info+']'
        return get_gpt_response(user_message=user_message, system_message=self.opts['text_system_message']+str(self.opts['max_products_per_page']), model=self.opts['model'])

    def get_product_attr_info(self):
        attr_info = self.find_first_n_attrs(tag=self.opts['attr_tag'], search_attrs=self.opts['search_attrs'], t=self.opts['attr_type'], html_tag_min=self.opts['html_tag_min']['attrs'], html_tag_limit=self.opts['html_tag_limit']['attrs'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+'\nURL: '+self.url+'\n\nPage HTML tag attributes:\n[\n'+attr_info+']'
        return get_gpt_response(user_message=user_message, system_message=self.opts['attr_system_message']+str(self.opts['max_products_per_page']), model=self.opts['model'])

    def update_with_attr_info(self, csv_text):
        attr_info = self.find_first_n_attrs(tag=self.opts['attr_tag'], search_attrs=self.opts['search_attrs'], t=self.opts['attr_type'], html_tag_min=self.opts['html_tag_min']['attrs'], html_tag_limit=self.opts['html_tag_limit']['attrs'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+"\nURL: "+self.url+'\n\nExtracted CSV:\n'+csv_text+"\n\nPage HTML tag attributes:\n[\n"+attr_info+"]"
        return get_gpt_response(user_message=user_message, system_message=self.opts['update_text_with_attr_system_message'], model=self.opts['model'])
    
    def update_with_text_info(self, csv_attr):
        text_info = self.find_first_n_texts(tag=self.opts['text_tag'], attrs=self.opts['text_attrs'], html_tag_min=self.opts['html_tag_min']['text'], html_tag_limit=self.opts['html_tag_limit']['text'])
        user_message = "Title: "+self.title+'\nQuery: '+self.query+"\nURL: "+self.url+'\n\nExtracted CSV:\n'+csv_attr+"\n\nPage HTML tag texts:\n[\n"+text_info+"]"
        return get_gpt_response(user_message=user_message, system_message=self.opts['update_attr_with_text_system_message'], model=self.opts['model'])

    def gpt_combine_text_and_attr_info(self, csv_text, csv_attr):
        user_message = "Title: "+self.title+'\nQuery: '+self.query+"\nURL: "+self.url+'\n\nExtracted CSV from Texts:\n'+csv_text+"\n\nExtracted CSV from Attributes:\n"+csv_attr
        return get_gpt_response(user_message=user_message, system_message=self.opts['combine_both_system_message'], model=self.opts['model'])

    #Not useful since Product URL cant be extracted with GPT due to excessive size
    def manual_combine_text_and_attr_info(self, csv_text, csv_attr):
        text_df = self.csv_to_df(csv_text)
        attr_df = self.csv_to_df(csv_attr)
        if self.opts['join_source'] == 'text':
            self.final_df = text_df.merge(attr_df, on='Product URL', how='inner')
        else:
            self.final_df = attr_df.merge(text_df, on='Product URL', how='inner')

    def find_product_urls(self):
        soup = BeautifulSoup(self.source)
        product_names = self.no_product_urls_df['Product Name'].tolist()
        all_url_tags = soup.find_all(re.compile('.*'), self.opts['product_url_attributes'])
        url_tag_children_texts = [[t.text for t in tag.find_all(re.compile('.*'))] for tag in all_url_tags] 
        urls = []
        for i in range(len(product_names)):
            matching_urls = [(j, all_tags.attrs['href'] if not all_tags.attrs['href'][0] == '/' else self.url_root+all_tags.attrs['href']) for j in range(len(all_tags_children_texts)) if self.contains_fuzzy_match(product_names[i], all_tags_children_texts[j])]
            if len(matching_urls) > 1:
                max_scores = [max([self.get_fuzzy_match_value(product_names[i], text) for text in all_tags_children_texts[url[0]]]) for url in matching_urls]
                urls.append([product_names[i], matching_urls[max_scores.index(max(max_scores))][1]])
            elif len(matching_urls) == 0:
                urls.append([product_names[i], 'None'])
            else:
                urls.append([product_names[i], matching_urls[0][1]])
        urls_df = pd.DataFrame(urls, columns=['Product Name', 'Product URL'])
        self.final_df = self.no_product_urls_df.merge(urls_df, on="Product Name")

    def contains_fuzzy_match(self, product_name, text_content):
        return any([self.fuzzy_match_product_names(product_name, name) for name in text_contents])
        

    def fuzzy_match_product_names(self, n1, n2):
        return self.get_fuzzy_match_value(n1, n2) >= self.opts['product_name_fuzzy_threshold']

    def get_fuzzy_match_value(self, n1, n2):
        return (fuzz.ratio(n1, n2)+fuzz.partial_ratio(n1, n2)+fuzz.token_sort_ratio(n1, n2))/3 

    def csv_to_df(self, csv):
        return pd.read_csv(StringIO(csv))




        

    #Use for grabbing html tags with useful text in them that contains things like price, product name, and rating
    #Text can be fed to GPT model for parsing into organized data
    def find_first_n_texts(self, tag, attrs, html_tag_min=100, html_tag_limit=500):
        soup = BeautifulSoup(self.source)
        tag_texts = [t.text.strip().strip('\n') for t in soup.find_all(tag, attrs) if t.text.strip('\n').strip() != '']
        tag_texts = [re.sub('\n\n*', ' ', t) for t in tag_texts]
        tag_texts = [t for t in tag_texts if (len(t) > self.opts['min_length']['text'] or self.has_currency(t)) and len(t) < self.opts['max_length']['text']]
        tag_texts = self.remove_duplicate_texts(tag_texts)
        tag_texts = [re.sub('out of 5 stars.*', 'stars', re.sub(r'(\$\d*\.\d\d)(\$\d*\.\d\d)', r'\1', t)) for t in tag_texts if "shipped by" not in t and "Free shipping" not in t and ("coupon" not in t and "checkout" not in t)]
        
        # tag_texts_nonempty = [t for t in a_tag_texts if t != '']
        return ',\n'.join(tag_texts[html_tag_min:html_tag_limit]) if len(tag_texts) > html_tag_limit else ',\n'.join(tag_texts)

    def remove_duplicate_texts(self, tag_texts):
        seen = set()
        new_list = []
        for t in tag_texts:
            if t not in seen and not self.has_currency(t):
                seen.add(t)
                new_list.append(t)
        return new_list

    def has_currency(self, t):
        return any([c in t for c in self.opts['currencies']])

    #Use for grabbing html tags with URLs in them and extracting those URLS
    #Can be fed to GPT model to match Product and Image URLS to their appropriate product entry, so long as enough attributes are given
    def find_first_n_attrs(self, tag, search_attrs, t, html_tag_min=0, html_tag_limit=70):
        soup = BeautifulSoup(self.source)
        tag_attrs = [{a:t.attrs[a] for a in self.opts['result_attrs'][t]} for t in soup.find_all(tag, search_attrs)]
        filtered_tag_attrs = self.filter_attrs(tag_attrs, t)
        return ',\n'.join(tag_attrs[html_tag_min:html_tag_limit]) if len(tag_attrs) > html_tag_limit else ',\n'.join(tag_attrs)
    
    def filter_attrs(self, tag_attr, t="image"):
        tag_attr_filtered = []
        for attrs in tag_attr:
            new_a = {}
            for k,v in attrs['attrs'].items():
                if len(v) > self.opts['min_length'][t] and k in self.opts['allowed_attrs'][t]:
                    new_a[k] = v
            if all([k in self.opts['allowed_attrs'][t] for k in attrs['attrs'].keys()]):
                tag_attr_filtered.append(new_a) 
        return self.remove_duplicate_attributes(tag_attr_filtered, t)

    def remove_duplicate_attributes(self, attribute_list, t):
        seen = set()
        new_list = []
        for d in attribute_list:
            if d[self.opts['attribute_primary_key'][t]] not in seen:
                seen.add(d[self.opts['attribute_primary_key'][t]])
                new_l.append(d)
        return new_l

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
            shop = Shop(url, self.shop_opts)
            self.shops.append(shop)
            self.shop_dfs.append(self.extract_shop_data(shop))



class MetaphorShopping():
    def __init__(self, metaphor, config_path):
        opts = load_config(config_path)
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
        self.searches[-1].build_user_question()
        self.searches[-1].get_urls()
        self.searches[-1].process_shops()
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





        





            



    

    
    

    
