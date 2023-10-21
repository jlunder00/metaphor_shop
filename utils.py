import socket
from urllib.parse import urlparse

def url_to_folder_name(url):
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
    folder_name = ip_address.replace(".", "_")

    return folder_name

def get_timestamp_fname(current_time, format, ftype):
    # Create a formatted filename
    filename = current_time.strftime(format)+ftype)
    return filename

def get_gpt_response(user_message, system_message, model):
    completion = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
                ]
            )
    return completion.choices[0].message.content

def get_metaphor_response(query, opts):
    return metaphor.search(query, use_autoprompt=opts['use_autoprompt'])

