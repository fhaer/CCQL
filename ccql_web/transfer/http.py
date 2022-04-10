import os
import sys
import subprocess
import shutil
import urllib.request
from bs4 import BeautifulSoup

from . import transfer_client as tc

class HttpClient(tc.TransferClient):
    
    CURL = "curl"
    WGET = "wget"

    def __init__(self, timestamp, protocol_name):
        super().__init__(timestamp, protocol_name)
    
    def copy_to_repository(self, files, repository_dir):
        print("Copy files to repository ...\n")
        os.chdir(self.init_dir)
        for f in files:
            if os.path.isfile(f):
                print("Copy", f, "to", repository_dir)
                shutil.copy(f, repository_dir)
            else:
                print("Error: file not found", f)
                sys.exit()
    
    def create_index_html(self, files, repository_dir):
        print("Creating index.html ...\n")
        os.chdir(self.repository_dir)
        with open("index.html", "w") as file:
            file.write("<!DOCTYPE html><html><head><title>File Index</title></head><body><ul>")
            for f in files:
                link = os.path.basename(f)
                file.write("<li><a href=\"" + link + "\">" + link + "</a></li>")
            file.write("</ul></body></html>")

    def curl_http_put(self, files, uri):
        os.chdir(self.repository_dir)
        addresses = []
        for f in files:
            print("\nUpload", f, "...")
            #subprocess.run([self.CURL, "-X", "POST", uri, "-F", "file=@/" + os.path.basename(f)])
            subprocess.run([self.CURL, "-T", os.path.basename(f), uri])
            address = uri + os.path.basename(f)
            print(address)
        subprocess.run([self.CURL, "-T", "index.html", uri])
        print("Upload finished")
        addresses.append(uri)
        return addresses
    
    def distribute(self, uri, files):
        print("\nDistribute using HTTP", uri, "\n")
        super().distribute()
        self.repository_dir = os.getcwd()

        self.copy_to_repository(files, self.repository_dir)
        self.create_index_html(files, self.repository_dir)

        addresses = self.curl_http_put(files, uri)
        os.chdir(self.init_dir)
        return addresses

    def ls_repository(self, repository_dir):
        files = []
        for f in os.listdir(repository_dir):
            if not f.endswith("index.html"):
                files.append(repository_dir + "/" + f)
        return files

    def retrieve(self, uri):
        print("\nRetrieve using HTTP", uri, "\n")
        super().retrieve()
        repository_dir = os.getcwd()

        parser = 'html.parser'
        resp = urllib.request.urlopen(uri)
        soup = BeautifulSoup(resp, parser, from_encoding=resp.info().get_param('charset'))

        for link in soup.find_all('a', href=True):
            file_uri = uri + link['href']
            subprocess.run([self.WGET, file_uri])

        os.chdir(self.init_dir)
        return self.ls_repository(repository_dir)
