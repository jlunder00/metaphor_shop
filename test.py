import pytest
from metaphor_python import Metaphor
from shop_data_extractor import MetaphorShopping, Shop

@pytest.fixture
def metaphor():
    # Create an instance of the Metaphor class
    return Metaphor("your_api_key")

@pytest.fixture
def metaphor_shopping(metaphor):
    # Create an instance of the MetaphorShopping class
    return MetaphorShopping(metaphor, 'config/config.yaml')

def test_metaphor_shopping_search(metaphor_shopping):
    # Perform a search and get the results
    product = "Halloween Costumes"
    pBrand = ""
    pStore = "Amazon"
    data = metaphor_shopping.perform_shop_search(product, pBrand, pStore)
    
    # Check that the data is returned as expected
    assert isinstance(data, pd.DataFrame)
    assert len(data) <= metaphor_shopping.opts["max_products_per_page"]

def test_shop_get_page(metaphor_shopping):
    # Create an instance of the Shop class
    url = "https://www.amazon.com"
    opts = metaphor_shopping.shop_opts
    shop = Shop(url, opts)
    
    # Get the page source
    shop.get_page()
    
    # Check that the source is not empty
    assert shop.source != ""
    
def test_shop_get_product_text_info(metaphor_shopping):
    # Create an instance of the Shop class
    url = "https://www.amazon.com"
    opts = metaphor_shopping.shop_opts
    shop = Shop(url, opts)
    
    # Get the product text information
    csv_text = shop.get_product_text_info()
    
    # Check that the CSV string is returned as expected
    assert isinstance(csv_text, str)
    assert "Product Name" in csv_text
    
def test_shop_get_product_attr_info(metaphor_shopping):
    # Create an instance of the Shop class
    url = "https://www.amazon.com"
    opts = metaphor_shopping.shop_opts
    shop = Shop(url, opts)
    
    # Get the product attribute information
    csv_attr = shop.get_product_attr_info()
    
    # Check that the CSV string is returned as expected
    assert isinstance(csv_attr, str)
    assert "Product Name" in csv_attr
    
def test_shop_find_product_urls(metaphor_shopping):
    # Create an instance of the Shop class
    url = "https://www.amazon.com"
    opts = metaphor_shopping.shop_opts
    shop = Shop(url, opts)
    
    # Set the source code and product names
    shop.source = """
        <html>
        <body>
        <h1>Product 1</h1>
        <a href="https://www.example.com/product1">Product 1 Link</a>
        <h1>Product 2</h1>
        <a href="https://www.example.com/product2">Product 2 Link</a>
        </body>
        </html>
    """
    shop.no_product_urls_df = pd.DataFrame({
        "Product Name": ["Product 1", "Product 2"]
    })
    
    # Find the product URLs
    shop.find_product_urls()
    
    # Check that the product URLs are extracted correctly
    assert shop.final_df.shape[0] == 2
    assert shop.final_df["Product URL"].iloc[0] == "https://www.example.com/product1"
    assert shop.final_df["Product URL"].iloc[1] == "https://www.example.com/product2"



#claude-2 tests:
import unittest
from shop_data_extractor import MetaphorShopping, MetaphorShoppingSearch, Shop  
from metaphor_python import Metaphor
import pandas as pd

class TestMetaphorShopping(unittest.TestCase):

    def setUp(self):
        # Initialize test objects
        self.metaphor = Metaphor("API_KEY") 
        self.metaphor_shopping = MetaphorShopping(self.metaphor, "config.yaml")

    def test_run_search(self):
        # Call run_search and verify dataframe is returned
        df = self.metaphor_shopping.run_search("halloween costumes")
        self.assertIsInstance(df, pd.DataFrame)
        
        # Verify dataframe has expected columns
        expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
        self.assertListEqual(list(df.columns), expected_cols)

    def test_perform_shop_search(self):
        # Call perform_shop_search and verify dataframe is returned
        df = self.metaphor_shopping.perform_shop_search("halloween costumes")
        self.assertIsInstance(df, pd.DataFrame)
        
        # Verify number of rows is less than max_products_per_page from config
        self.assertLessEqual(len(df), self.metaphor_shopping.opts['max_products_per_page'])

        # Verify dataframe has expected columns
        expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
        self.assertListEqual(list(df.columns), expected_cols)

class TestMetaphorShoppingSearch(unittest.TestCase):

    def setUp(self):
        self.metaphor = Metaphor("API_KEY")
        self.search = MetaphorShoppingSearch("costume", "", "Amazon", self.metaphor, {}, {})

    def test_get_urls(self):
        # Call get_urls and verify list of urls is returned
        urls = self.search.get_urls()
        self.assertIsInstance(urls, list)
        self.assertTrue(all(isinstance(url, str) for url in urls))
        
        # Verify urls look valid
        self.assertTrue(all("http" in url for url in urls))

    @unittest.skip("Need real website for test")
    def test_extract_shop_data(self):
        # Extract data from sample website and verify dataframe returned
        url = "PUT_A_REAL_WEBSITE_HERE" 
        shop = Shop(url, {})
        df = self.search.extract_shop_data(shop)
        
        self.assertIsInstance(df, pd.DataFrame)
        
        # Verify dataframe has expected columns
        expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
        self.assertListEqual(list(df.columns), expected_cols)
        
class TestShop(unittest.TestCase):

    def setUp(self):
        self.url = "PUT_A_REAL_WEBSITE_HERE"
        self.shop = Shop(self.url, {})

    @unittest.skip("Need real website for test")
    def test_get_products(self):
        # Call get_products and verify dataframe is set
        self.shop.get_products()
        self.assertIsInstance(self.shop.final_df, pd.DataFrame)

        # Verify dataframe has expected columns
        expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"] 
        self.assertListEqual(list(self.shop.final_df.columns), expected_cols)

    def test_csv_to_df(self):
        # Pass sample CSV text and verify dataframe created
        csv_text = '"Product Name";"Price"\n"Foo";"19.99"\n"Bar";"29.99"'
        df = self.shop.csv_to_df(csv_text)
        
        self.assertIsInstance(df, pd.DataFrame)
        
        # Verify dataframe has expected columns
        expected_cols = ["Product Name", "Price"]
        self.assertListEqual(list(df.columns), expected_cols)

        # Verify row count
        self.assertEqual(len(df), 2)

if __name__ == '__main__':
    unittest.main()
