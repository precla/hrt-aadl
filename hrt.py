#!/usr/bin/env python3
"""HRT Audio archive downloader"""

import argparse
import os
import re
import requests

PARSER = argparse.ArgumentParser(description='Download audio files from radio archive of HRT.')

PARSER.add_argument('-u', metavar='URL', type=str, required=True,
                    help="url for example: http://radio.hrt.hr/emisija/govorimo-hrvatski/200/")
PARSER.add_argument('-d', metavar='DIRECTORY', type=str, required=False,
                    help="set destination directory, default is current directory of this .py file")
PARSER.add_argument('-v', '--version', action="version", version="%(prog)s 0.1.2")
# Todo: make it possible to dl only a specified amount:
# PARSER.add_argument('-n', type=int, help="number of files to download", default=0, required=False)

def main():
    """Where it all begins"""

    args = PARSER.parse_args()

    # just a quick check to see if the user provided an acceptable link
    if r"http://radio.hrt.hr/arhiva/" in args.u or r"http://radio.hrt.hr/emisija/" in args.u or r"http://radio.hrt.hr/ep/" in args.u:
        response_hrt = requests.get(args.u)
        response_hrt = response_hrt.text
    else:
        print("This Link is not valid!")
        return

    # Exclude 'Najave' (engl.: upcoming), beacuse those don't have a dl link
    # "col-md-8" - /arhiva/ , "col-sm-8" - /emisija/
    # if it is a link to a singel ep only, than dl that one directly and exit
    if r"http://radio.hrt.hr/arhiva/" in args.u:
        response_hrt = response_hrt[response_hrt.find("col-md-8") + 8: response_hrt.find("col-sm-4 side-widgets")]
    elif r"http://radio.hrt.hr/emisija/" in args.u:
        response_hrt = response_hrt[response_hrt.find("col-sm-8") + 8 : response_hrt.find("col-sm-4 side-widgets")]
    elif r"http://radio.hrt.hr/ep/" in args.u:
        link = args.u[19:]
        grab_file(link, args.d)
        return

    # prepare regex for /ep/dogodilo-se-na-danasnji-dan-24-04/201535/ and similiar
    regexcheck = re.compile(r"/ep/\S+/\"")

    # check with regex and save all matches in a list
    list_of_matches = list(set(regexcheck.findall(response_hrt)))

    # iterate trought list and send it to grab_file to dl the mp3
    for link in list_of_matches:
        link = link.replace("\"", "")
        grab_file(link, args.d)

    #print(list_of_matches)

def grab_file(link, dl_dir):
    """download file for each link"""
    # add prefix so the link is valid
    link = "http://radio.hrt.hr" + link

    # find the title and link to download the *.mp3
    response_download = requests.get(link)
    if response_download.status_code != 200:
        print("Error while trying to reach the link")

    response_download = response_download.text

    # find track title
    regexcheck = re.compile(r"track-title\">([\w\s\-]+)", re.UNICODE)
    track_title = list(set(regexcheck.findall(response_download)))

    # find the link for the *.mp3
    regexcheck = re.compile(r"href=\"(\S+.mp3)")
    mp3_link = list(set(regexcheck.findall(response_download)))
    mp3_link = "http://radio.hrt.hr" + mp3_link[0]

    # save to current working directory if user did not specify a directory
    if not dl_dir:
        dl_dir = os.getcwd()

    dl_dir = os.path.normpath(dl_dir)
    dl_dir = dl_dir + "\\"

    response_download = requests.get(mp3_link)
    with open(dl_dir + track_title[0] + ".mp3", 'wb') as file_dl:
        file_dl.write(response_download.content)

if __name__ == "__main__":
    main()
