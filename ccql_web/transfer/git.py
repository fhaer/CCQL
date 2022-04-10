import os
import subprocess
import sys
import shutil
import re

from . import transfer_client as tc

class GitClient(tc.TransferClient):
    
    GIT = "git"

    def __init__(self, timestamp, protocol_name):
        super().__init__(timestamp, protocol_name)

    def get_repository_dir(self, repository_uri):
        dir_name = re.sub(r".git$", "", repository_uri)
        dir_name = re.sub(r"^.*\/", "", dir_name)
        dir_name = re.sub(r"[^\w-]", "", dir_name)
        return self.working_dir + "/" + dir_name

    def copy_to_repository(self, files, repository_dir):
        print("\nCopy files to repository ...\n")
        os.chdir(self.init_dir)
        for f in files:
            if os.path.isfile(f):
                print("Copy", f, "to", repository_dir)
                shutil.copy(f, repository_dir)
            else:
                print("Error: file not found", f)
                sys.exit()
    
    def git_fetch_merge(self, repository_dir):
        os.chdir(repository_dir)
        print("\nGit fetch ...\n")
        subprocess.run([self.GIT, "fetch", "-v"])
        print("\nGit merge ...\n")
        subprocess.run([self.GIT, "merge"])
        os.chdir(self.init_dir)

    def git_clone(self, repository_uri, repository_dir):
        os.makedirs(repository_dir, exist_ok=True)
        print("\nGit clone ...\n")
        subprocess.run([self.GIT, "clone", repository_uri, repository_dir])
        subprocess.run([self.GIT, "init", repository_dir])

    def git_add(self, files, repository_dir):
        os.chdir(repository_dir)
        print("\nGit add ...\n")
        for f in files:
            file_name = os.path.basename(f)
            if os.path.isfile(file_name):
                print("add", file_name)
                subprocess.run([self.GIT, "add", file_name])
        os.chdir(self.init_dir)

    def git_commit_push(self, repository_dir, repository_uri):
        os.chdir(repository_dir)
        print("\nGit commit ...\n")
        subprocess.run([self.GIT, "commit", "-m", "files for remote distribution"])
        print("\nGit push ...\n")
        subprocess.run([self.GIT, "push", repository_uri])
        os.chdir(self.init_dir)

    def distribute(self, repository_uri, files):
        print("\nDistribute files using Git to", repository_uri, "...\n")

        repository_dir = self.get_repository_dir(repository_uri)

        print("Repository located at", repository_dir, "\n")
        if os.path.isdir(repository_dir):
            self.git_fetch_merge(repository_dir)
        else:
            self.git_clone(repository_uri, repository_dir)

        if os.path.isdir(repository_dir + "/.git"):
            self.copy_to_repository(files, repository_dir)
            self.git_add(files, repository_dir)
            self.git_commit_push(repository_dir, repository_uri)
        else:
            print("Error: unable to access repository", repository_dir)
            sys.exit()
        
        os.chdir(self.init_dir)
        addresses = [repository_uri]
        return addresses

    def ls_repository(self, repository_dir):
        files = []
        for f in os.listdir(repository_dir):
            if not f.endswith(".git"):
                files.append(repository_dir + "/" + f)
        return files

    def retrieve(self, repository_uri):
        print("\nRetrieve using Git from", repository_uri, "\n")

        repository_dir = self.get_repository_dir(repository_uri)

        print("\nRepository located at", repository_dir, "\n")
        if os.path.isdir(repository_dir):
            self.git_fetch_merge(repository_dir)
        else:
            self.git_clone(repository_uri, repository_dir)
        
        return self.ls_repository(repository_dir)

