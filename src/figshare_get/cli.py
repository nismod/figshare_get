"""Download files from a figshare collection

See https://docs.figshare.com/ for API documentation.

This script makes three API calls: search for a collection, to get the ID;
request metadata about all articles in the collection; request metadata about
all files in each article.

Then it uses the "download_url" and "name" of each file to download and save to
the working directory.
"""
import argparse
import json
import os
import sys

import requests


def figshare_get(args=None):
    parser = argparse.ArgumentParser(prog="figshare_get")
    parser.add_argument(
        "search",
        type=str,
        help="Search using a DOI or description of a figshare collection to download",
    )
    parser.add_argument(
        "-n",
        "--result-number",
        required=False,
        type=int,
        help="Download result number (0-9) without prompting",
    )
    args = parser.parse_args(args)

    results = search(args.search)
    if "message" in results:
        print(results)
        sys.exit()
    elif len(results):
        if args.result_number is not None:
            result = results[args.result_number]
        else:
            for i, result in enumerate(results):
                print("  ", i, result["title"], result["doi"])
            result_num_str = input(
                "Type the number of a result to download, or ENTER to skip\n"
            )
            if not len(result_num_str):
                sys.exit()
            else:
                try:
                    result_num = int(result_num_str)
                    result = results[result_num]
                except:
                    print("Did not provide a number in range")
                    sys.exit()

    else:
        print("No results")
        sys.exit()

    collection_id = result["id"]
    download_collection_meta(collection_id)
    download_collection_files(collection_id)


def download_collection_meta(collection_id):
    meta = get_collection(collection_id)
    fname = f"metadata_{collection_id}.json"
    print("Saving metadata to", fname)
    with open(fname, "w") as fd:
        json.dump(meta, fd, indent=2)


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


def search(string):
    url = "https://api.figshare.com/v2/collections/search"
    data = {"search_for": string}
    r = requests.post(url, data=json.dumps(data))
    return r.json()


def get_collection(collection_id):
    url = f"https://api.figshare.com/v2/collections/{collection_id}"
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
