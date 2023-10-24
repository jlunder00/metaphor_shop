from metaphor_python import Metaphor
import unittest
from shop_data_extractor import MetaphorShopping, MetaphorShoppingSearch, Shop  
import pandas as pd
import os
from utils import *

class TestMetaphorShopping(unittest.TestCase):

    def setUp(self):
        # Initialize test objects
        self.metaphor = Metaphor("METAPHOR_API_KEY") 
        self.metaphor_shopping = MetaphorShopping(self.metaphor, "config.yaml")
        self.product = "Halloween Costumes"
        self.pBrand = ''
        self.pStore = 'Amazon'

    def test_run_search(self):
        # Call run_search and verify dataframe is returned
        self.metaphor_shopping.run_search(product=self.product, pBrand=self.pBrand, pStore=self.pStore)
        df = self.metaphor_shopping.data
        self.assertIsInstance(df, pd.DataFrame)
        
        # Verify dataframe has expected columns
        expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
        self.assertListEqual(list(df.columns), expected_cols)

    def test_perform_shop_search(self):
        # Call perform_shop_search and verify dataframe is returned
        self.metaphor_shopping.perform_shop_search(self.product, self.pBrand, self.pStore)
        df = self.metaphor_shopping.data
        self.assertIsInstance(df, pd.DataFrame)
        
        # Verify number of rows is less than max_products_per_page from config
        self.assertLessEqual(len(df), self.metaphor_shopping.opts['max_products_per_page'])

        # Verify dataframe has expected columns
        expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
        self.assertListEqual(list(df.columns), expected_cols)

class TestMetaphorShoppingSearch(unittest.TestCase):

    def setUp(self):
        self.metaphor = Metaphor("METAPHOR_API_KEY")
        self.product = "Halloween Costumes"
        self.pBrand = ''
        self.pStore = 'Amazon'
        self.overall_opts = load_config('config/test_config.yaml') 
        self.search = MetaphorShoppingSearch(self.product, self.pBrand, self.pStore, self.metaphor, overall_opts['metaphor_shop_search'], overall_opts['metaphor_shop'])

    def test_get_urls(self):
        # Call get_urls and verify list of urls is returned
        self.search.get_urls()
        urls = self.search.urls
        self.assertIsInstance(urls, list)
        self.assertTrue(all(isinstance(url, str) for url in urls))
        
        # Verify urls look valid
        self.assertTrue(all("http" in url for url in urls))

    # @unittest.skip("Need real website for test")
    def test_extract_shop_data(self):
        # Extract data from sample website and verify dataframe returned
        url = "https://www.amazon.com/s?k=halloween+costumes" 
        shop = Shop(url, self.overall_opts['shop'])
        df = self.search.extract_shop_data(shop)
        
        self.assertIsInstance(df, pd.DataFrame)
        
        # Verify dataframe has expected columns
        expected_cols = ["Product Name", "Product URL", "Product Image", "Price", "Rating"]
        self.assertListEqual(list(df.columns), expected_cols)
        
class TestShop(unittest.TestCase):

    def setUp(self):
        self.url = "https://www.amazon.com/s?k=halloween+costumes"
        self.overall_opts = load_config('config/test_config.yaml') 
        self.shop = Shop(self.url, self.overall_opts['shop'])

    def test_shop_get_page(self):
        shop.get_page()

        self.assertNotEqual(self.shop.source, "")
        self.assertIsInstance(self.shop.source, str)

    def test_shop_get_product_text_info(self):
        csv_text = self.shop.get_product_text_info()

        self.assertIsInstance(csv_text, str)
        self.assertIn("Product Name", str)

    def test_shop_get_product_attr_info(self):
        csv_text = self.shop.get_product_attr_info()

        self.assertIsInstance(csv_text, str)
        self.assertIn("Product Name", str)

    def test_shop_find_product_urls(self):
        # Using an example html page for testing to ensure fuzzy search finds the right name/url
        # Create a mock instance of the Shop class
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
        self.assertEqual(shop.final_df.shape[0], 2)
        self.assertEqual(shop.final_df["Product URL"].iloc[0], "https://www.example.com/product1")
        self.assertEqual(shop.final_df["Product URL"].iloc[1], "https://www.example.com/product2")

    # @unittest.skip("Need real website for test")
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
