import os
import pytest
import pandas as pd
from utils import *
import logging
from shop_data_extractor import MetaphorShopping, MetaphorShoppingSearch, Shop
from metaphor_python import Metaphor

# Set up the logging configuration
log_file = "app.log"  # File to log to
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@pytest.fixture
def metaphor_shopping():
    metaphor = Metaphor(os.environ.get("METAPHOR_API_KEY"))
    return MetaphorShopping(metaphor, "config/test_config.yaml")

@pytest.fixture
def metaphor_shopping_search():
    metaphor = Metaphor(os.environ.get("METAPHOR_API_KEY"))
    product = "Halloween Costumes"
    pBrand = ''
    pStore = 'Amazon'
    overall_opts = load_config('config/test_config.yaml')
    return MetaphorShoppingSearch(product, pBrand, pStore, metaphor, overall_opts['metaphor_shop_search'], overall_opts['shop'])

@pytest.fixture
def shop():
    url = "https://www.amazon.com/s?k=halloween+costumes"
    overall_opts = load_config('config/test_config.yaml')
    opts = overall_opts['shop']
    return Shop(url, opts)

def test_perform_shop_search(metaphor_shopping):
    product = "Halloween Costumes"
    pBrand = ''
    pStore = 'Amazon'
    data = metaphor_shopping.perform_shop_search(product, pBrand, pStore)
    assert isinstance(data, pd.DataFrame)
    expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
    # assert list(data.columns) == expected_cols
    assert all([item in expected_cols for item in list(data.columns)])
    assert all([item in list(data.columns) for item in expected_cols])

def test_get_urls(metaphor_shopping_search):
    search = metaphor_shopping_search
    search.get_urls()
    urls = search.urls
    assert isinstance(urls, list)
    assert all(isinstance(url, str) for url in urls)
    assert all("http" in url for url in urls)

def test_search(metaphor_shopping_search):
    search = metaphor_shopping_search
    search.urls = ['https://www.amazon.com/s?k=halloween+costumes']
    search.process_shops()
    dfs = search.shop_dfs
    df = dfs[0]
    assert isinstance(df, pd.DataFrame)
    expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
    assert all([item in expected_cols for item in list(df.columns)])
    assert all([item in list(df.columns) for item in expected_cols])

def test_shop_get_page(shop):
    shop.get_page()
    assert shop.source != ""
    assert isinstance(shop.source, str)

# Mark methods involving real network requests as skipped by default.
@pytest.mark.skip("Skip GPT requests while debugging")
def test_shop_extract_product_attr_info(shop):
    shop.get_page()
    csv_text = shop.get_product_attr_info()
    assert isinstance(csv_text, str)
    assert "Product Name" in csv_text

@pytest.mark.skip("Skip GPT requests while debugging")
def test_shop_extract_product_text_info(shop):
    shop.get_page()
    csv_text = shop.get_product_text_info()
    assert isinstance(csv_text, str)
    assert "Product Name" in csv_text

@pytest.mark.skip("Skip GPT requests while debugging")
def test_shop_update_attr_with_text(shop):
    shop.get_page()
    csv_text = shop.get_product_attr_info()
    csv_text = shop.update_with_text_info(csv_text)
    assert isinstance(csv_text, str)
    assert "Product Name" in csv_text
    assert "Image URL" in csv_text

def test_shop_filter_attr_info(shop):
    shop.get_page()
    attr_info = shop.find_first_n_attrs(tag=shop.opts['attr_tag'], search_attrs=shop.opts['search_attrs'], type_=shop.opts['attr_type'], html_tag_min=shop.opts['html_tag_min']['attrs'], html_tag_limit=shop.opts['html_tag_limit']['attrs'])
    assert isinstance(attr_info, str)
    assert attr_info != ""

def test_shop_filter_text_info(shop):
    shop.get_page()
    text_info = shop.find_first_n_texts(tag=shop.opts['text_tag'], attrs=shop.opts['text_attrs'], html_tag_min=shop.opts['html_tag_min']['text'], html_tag_limit=shop.opts['html_tag_limit']['text'])
    assert isinstance(text_info, str)
    assert text_info != ""

def test_shop_find_product_urls(shop):
    # Using an example HTML page for testing to ensure fuzzy search finds the right name/url
    shop.url = "https://www.amazon.com"
    shop.source = """
        <html>
        <body>
        <a href="https://www.example.com/product1">
        <a class="something">Product 1</a>
        </a>
        <a href="https://www.example.com/product2">
        <a class="something">Product 2</a>
        </a>
        </body>
        </html>
    """
    shop.no_product_urls_df = pd.DataFrame({
        "Product Name": ["Product 1", "Product 2"]
    })

    shop.find_product_urls()
    assert shop.final_df.shape[0] == 2
    assert shop.final_df["Product URL"].iloc[0] == "https://www.example.com/product1"
    assert shop.final_df["Product URL"].iloc[1] == "https://www.example.com/product2"

@pytest.mark.skip("Need real website for test")
def test_get_products(shop):
    shop.get_products()
    assert isinstance(shop.final_df, pd.DataFrame)
    expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
    # assert list(shop.final_df.columns) == expected_cols
    assert all([item in expected_cols for item in list(shop.final_df.columns)])
    assert all([item in list(shop.final_df.columns) for item in expected_cols])

def test_csv_to_df(shop):
    csv_text = '"Product Name";"Price"\n"Foo";"19.99"\n"Bar";"29.99"'
    df = shop.csv_to_df(csv_text)
    assert isinstance(df, pd.DataFrame)
    expected_cols = ["Product Name", "Price"]
    assert list(df.columns) == expected_cols
    assert len(df) == 2

