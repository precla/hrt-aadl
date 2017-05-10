#!/usr/bin/env python3
"""HRT Audio archive downloader"""

import argparse
import os
import requests
from bs4 import BeautifulSoup
from slugify import slugify
from tqdm import tqdm

# arguments parser:
PARSER = argparse.ArgumentParser(description='Download audio files from radio archive of HRT.')
PARSER.add_argument('-u', metavar='URL', type=str, required=True,
                    help="url for example: http://radio.hrt.hr/emisija/govorimo-hrvatski/200/")
PARSER.add_argument('-d', metavar='DIRECTORY', type=str, required=False,
                    help="set destination directory, default is current directory of this .py file")
PARSER.add_argument('-v', '--version', action="version", version="%(prog)s 0.2.0")
# Todo: make it possible to dl only a specified amount:
# PARSER.add_argument('-n', type=int, help="number of files to download", default=0, required=False)

def main():
    """Where it all begins"""

    args = PARSER.parse_args()

    # just a quick check to see if the user provided an acceptable link
    # and that the link was reachable
    if r"http://radio.hrt.hr/arhiva/" in args.u or r"http://radio.hrt.hr/emisija/" in args.u:
        response_hrt = requests.get(args.u)
        # 'dirty workaround' to remove the following warning:
        # [pylint] E1101:Instance of 'LookupDict' has no 'ok' member
        #pylint: disable=maybe-no-member
        if response_hrt.status_code != requests.codes.ok:
            response_hrt.raise_for_status()
            return

        response_hrt = response_hrt.text
        soup = BeautifulSoup(response_hrt, "html.parser")

        episode_link = []
        episode_title = []

        # class_="media-heading" -> this excludes 'Najave' (engl.: upcoming/sheduled)
        # beacuse those don't have a dl link
        for link in soup.find_all(class_="media-heading"):
            # link to episode
            episode_link.append(link.contents[0].attrs['href'])
            # episode title
            episode_title.append(link.string)
    else:
        print("This Link is not valid!")
        return

    # save to the current working directory if the user did not specify a folder and
    # create the folder if it doesn't exist
    if not args.d:
        dl_dir = os.getcwd()
    else:
        dl_dir = args.d
        if not os.path.exists(dl_dir):
            os.makedirs(dl_dir)

    dl_dir = os.path.normpath(dl_dir)
    dl_dir = dl_dir + "\\"

    # iterate trought the list of links and send it to grab_file(...) to dl the mp3
    for (link, title) in zip(episode_link, episode_title):
        grab_file(link, title, dl_dir)

def grab_file(link, title, dl_dir):
    """download file for each link"""
    # add prefix so the link is valid
    link = "http://radio.hrt.hr" + link

    # find the title and link to download the *.mp3
    response_download = requests.get(link)

    # 'dirty workaround' to remove the following warning:
    # [pylint] E1101:Instance of 'LookupDict' has no 'ok' member
    #pylint: disable=maybe-no-member
    if response_download.status_code != requests.codes.ok:
        print("Error while trying to reach the link")

    response_download = response_download.text

    # remove characters that are not supported in file names from the title:
    track_title = slugify(title)

    # find the link for the *.mp3 -> class="attachment-file"
    soup = BeautifulSoup(response_download, "html.parser")
    for link in soup.find_all(class_="download-section"):
        # file_size = link.contents[3].contents[3].string
        mp3_link = "http://radio.hrt.hr" + link.contents[3].attrs['href']

    response_download = requests.get(mp3_link, stream=True)
    # convert the number of bytes into chunks (pieces)
    f_size = int(response_download.headers.get('content-length', 0)) / (32*1024)

    print("Downloading: '" + title + "'")

   # fire up the progress bar with tqdm
    with open(dl_dir + track_title + ".mp3", "wb") as file_dl:
        for data in tqdm(response_download.iter_content(32*1024), total=f_size, unit='chunk', unit_scale=True):
            file_dl.write(data)

if __name__ == "__main__":
    main()
