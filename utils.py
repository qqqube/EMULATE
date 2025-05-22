import configparser
import http.client
import json
import requests
import html2text
from agents import WebPageExtractor


# ------ Login Helper Functions -------------------------------------

def get_credentials(credentials_path):
    """
    Credentials INI file should look like:

    [BASIC]
    SERPER_API_KEY = <api_key>
    OPENAI_API_KEY = <api_key>
    """
    config = configparser.ConfigParser()
    config.read(credentials_path)
    return config["BASIC"]["SERPER_API_KEY"], config["BASIC"]["OPENAI_API_KEY"]


# -------- Serper Search Engine API -------------------------------------

class SerperResult():

    def __init__(self, _dict):
        self.title = _dict["title"]
        self.link = _dict["link"]
        self.snippet = _dict["snippet"]
        self.position = _dict["position"]
    
    def __str__(self):
        return f"position: {self.position} \ntitle: {self.title} \nlink: {self.link}\nsnippet: {self.snippet}"
    
    def visit_web_page(self, client, openai_model_name, use_webextraction_agent):
        """ 
        Convert URL content into string. 
        Set self.content to extracted content or self.snippet 
        """
        if use_webextraction_agent:
            try:
                response = requests.get(self.link)
                h = html2text.HTML2Text()
                h.ignore_links = True
                ascii_text = h.handle(response.text)
                self.content = WebPageExtractor(client, openai_model_name, self.link, ascii_text)
            except Exception:
                self.content = self.snippet
        else:
            self.content = self.snippet
    
    def make_into_memory(self):
        """At this point, self.content should be populated"""
        return f"Title: {self.title} \nURL: {self.link} \nContent: {self.content}"

class Serper():

    def __init__(self, api_key):
        self.api_key = api_key
    
    def query(self, _query):
        """ Return list of SerperResult instances sorted by position """
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({"q": _query})
        headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()
        results = json.loads(data.decode("utf-8"))
        results = [SerperResult(item) for item in results['organic'] if "snippet" in item.keys()]
        results.sort(key=lambda item : item.position)
        return results

