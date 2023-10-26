import socket
from urllib.parse import urlparse
from omegaconf import OmegaConf
import re
import openai

#Use this to select all the tags that have some sort of URL in their attributes, 
#then later filter out those that dont have attrs that include any of the product names previously found
def url_selector(tag):
    return tag.name == 'img' or tag.has_attr('href') or (tag.has_attr('alt') and tag.has_attr('src'))

def image_url_selector(tag):
    return tag.has_attr('alt') and tag.has_attr('src')

SEARCH_ATTR_SWITCH = {
        'url_selector':url_selector,
        'image_url_selector':image_url_selector
        }


def url_to_name(url):
    # Parse the URL to get the hostname
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc

    # Get the IP address for the hostname
    try:
        ip_address = socket.gethostbyname(hostname)
    except socket.gaierror:
        # Handle the case where the URL couldn't be resolved to an IP address
        ip_address = "unknown"

    # Remove any dots in the IP address to create a valid folder name
    name = ip_address.replace(".", "_")

    return name

# def get_timestamp_fname(current_time, format, ftype):
#     # Create a formatted filename
#     filename = current_time.strftime(format)+ftype)
#     return filename

def get_gpt_response(user_message, system_message, model):
    completion = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
                ]
            )
    return completion.choices[0].message.content

def get_metaphor_response(metaphor, query, opts):
    print('METAPHOR HEADERS:', metaphor.headers)
    return [s.url for s in metaphor.search(query, use_autoprompt=opts['use_autoprompt']).results][:opts['max_urls']]
    

def load_config(config_file):
    conf = OmegaConf.load(config_file)
    config = OmegaConf.to_container(conf, resolve=True)
    if config['shop']["text_tag"] == 'all':
        config['shop']['text_tag'] = re.compile(".*")

    if config['shop']["attr_tag"] == 'all':
        config['shop']['attr_tag'] = re.compile(".*")

    config['shop']['search_attrs'] = SEARCH_ATTR_SWITCH[config['shop']['search_attrs']]

    return config
    


