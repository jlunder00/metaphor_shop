from shop_data_extractor import MetaphorShopping
import streamlit as st
from metaphor_python import Metaphor
import os

def main():
    st.title("Metaphor Shop")
    metaphor = Metaphor(os.environ.get("METAPHOR_API_KEY"))
    metaphor_shopping_page = MetaphorShopping(metaphor, os.environ.get("CONFIG_PATH"))
    #get product
    #get brand
    #get store
    product = 'Halloween Cosutmes'
    pBrand = ''
    pStore = 'Amazon'
    metaphor_shopping_page.run_search(product, pBrand, pStore)

if __name__=='__main__':
    main()
     
