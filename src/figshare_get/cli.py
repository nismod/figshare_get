"""Download files from a figshare collection

See https://docs.figshare.com/ for API documentation.

This script makes a series of API calls:
- search for an article or collection by DOI, to get the ID;
- request metadata about the article, or all articles in the collection;
- request metadata about all files in each article.

Then it uses the "download_url" and "name" of each file to download and save to
the working directory.
"""

import argparse
import json
import os
import sys

import requests


def figshare_get(args=None):
    try:
        parser = argparse.ArgumentParser(prog="figshare_get")
        parser.add_argument(
            "doi",
            type=str,
            help="Search using the DOI of a figshare collection or article to download",
        )
        args = parser.parse_args(args)

        # search articles
        articles = search_articles(args.doi)
        result = check_results(articles)

        # if found, download then quit
        if result is not None:
            id_ = result["id"]
            print("Downloading from", result["doi"], result["title"])
            download_article_meta(id_)
            download_article_files(id_)
            sys.exit()

        # else search collections
        collections = search_collections(args.doi)
        result = check_results(collections)

        if result is None:
            print("Not found")
            sys.exit()

        id_ = result["id"]
        print("Downloading from", result["doi"], result["title"])
        download_collection_meta(id_)
        download_collection_files(id_)
    except KeyboardInterrupt:
        pass
    finally:
        pass


def check_results(results):
    if "message" in results:
        print(results)
        sys.exit()
    elif len(results):
        result = results[0]
    else:
        result = None
    return result


def download_article_meta(article_id):
    meta = get_article(article_id)
    fname = f"metadata_{article_id}.json"
    print("Saving metadata to", fname)
    with open(fname, "w") as fd:
        json.dump(meta, fd, indent=2)


def download_collection_meta(collection_id):
    meta = get_collection(collection_id)
    fname = f"metadata_{collection_id}.json"
    print("Saving metadata to", fname)
    with open(fname, "w") as fd:
        json.dump(meta, fd, indent=2)


def download_article_files(article_id):
    for file_meta in get_article_files(article_id):
        fname = file_meta["name"]
        if os.path.exists(fname):
            print("Skipping", fname)
        else:
            print("Downloading", fname)
            save_file(file_meta)


def download_collection_files(collection_id):
    for file_meta in get_collection_files(collection_id):
        fname = file_meta["name"]
        if os.path.exists(fname):
            print("Skipping", fname)
        else:
            print("Downloading", fname)
            save_file(file_meta)


def get_collection_files(collection_id):
    article_ids = get_collection_articles(collection_id)
    for article_id in article_ids:
        file_metadata = get_article_files(article_id)
        for file_meta in file_metadata:
            yield file_meta


def search_articles(string):
    url = "https://api.figshare.com/v2/articles/search"
    data = {"doi": string}
    r = requests.post(url, data=json.dumps(data))
    return r.json()


def search_collections(string):
    url = "https://api.figshare.com/v2/collections/search"
    data = {"doi": string}
    r = requests.post(url, data=json.dumps(data))
    return r.json()


def get_collection(collection_id):
    url = f"https://api.figshare.com/v2/collections/{collection_id}"
    r = requests.get(url)
    data = r.json()
    return data


def get_article(article_id):
    url = f"https://api.figshare.com/v2/articles/{article_id}"
    r = requests.get(url)
    data = r.json()
    return data


def get_collection_articles(collection_id):
    url = f"https://api.figshare.com/v2/collections/{collection_id}/articles?page_size=1000"
    r = requests.get(url)
    data = r.json()
    return [article["id"] for article in data]


def get_article_files(article_id):
    url = f"https://api.figshare.com/v2/articles/{article_id}/files"
    r = requests.get(url)
    data = r.json()
    return data


def save_file(file_meta):
    r = requests.get(file_meta["download_url"], stream=True)
    with open(file_meta["name"], "wb") as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)
