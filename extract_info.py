import os
import openai
from metaphor_python import Metaphor
from bs4 import BeautifulSoup
from selenium import webdriver

openai.api_key =  os.getenv("OPENAI_API_KEY")

metaphor = Metaphor(os.getenv("METAPHOR_API_KEY"))



def build_user_question(product, pBrand, pStore):
    return product+("\nPreferred Brand: "+pBrand if pBrand is not None else "")+("\nPreferred Store: "+pStore if pStore is not None else "")

def get_urls(metaphor, user_question):
    SYSTEM_MESSAGE = "You are a helpful assistant that generates shopping related search queries based on user questions. Generate one and only one search query to find products the user might like to buy. Generate queries searching for pages where you can buy products that a company is advertising. If the user has a preferred store or brand, specified by "preferred store: x" or "preferred brand: x" after the prompt, include that in the query naturally. if none are specified, do not include it in the query."

    completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_question}
                ]
            )

    query = completion.choices[0].message.content
    search_response = metaphor.search(
            query, use_autoprompt=True
            )
    print(f"URLs: {[result.url for result in search_response.results]}\n")
    return search_response, query

#Price extraction and organization
# def extract_price(url, webpage, query):
#     SYSTEM_MESSAGE = "You are a helpful assistant that identifies and extracts the price of a product contained in a webpage, given the HTML source of that webpage. Find and return the numerical price of the product on the page, in US dollars, as a number. Report only one price. If no prices or products are present, return -1. If multiple prices or products are present, use the query that was used to find the webpage and the URL of the webpage to disambiguate and return the price of the product most likely to be the focus of the webpage."
#     user_message = "webpage source:\n"+webpage+"\n\nquery used: "+query+"\nURL: "+url
#     completion = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[
#                 {"role": "system", "content": SYSTEM_MESSAGE},
#                 {"role": "user", "content": user_message}
#                 ]
#             )






#Use this to select all the tags that have some sort of URL in their attributes, 
#then later filter out those that dont have attrs that include any of the product names previously found
def url_selector(tag):
    return tag.name == 'img' or tag.has_attr('href') or tag.has_attr('alt') or tag.has_attr('src')



# Use selenium to load page content then use this with beautiful soup to extract names, product page urls, and image urls (needs work)
#'\n'.join([json.dumps({'alt':item.attrs['alt'], 'src':item.attrs['src'], 'string': item.string}) for item in soup.find_all("img", alt=True, src=True)]+[json.dumps({'title':item.attrs['title'], 'href':item.attrs['href'], 'string': item.string}) for item in soup.find_all('a', href=True, title=True)])
