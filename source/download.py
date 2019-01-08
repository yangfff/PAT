#! /usr/bin/env python3
import os
import sys
import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import argparse
import logging
import config

class PATDownloader:
    def __init__(self, force):
        self._force = force
        options = Options()
        options.headless = True
        self._phantomBrowser = webdriver.Firefox(options=options)
        self._baseUrl = "https://pintia.cn"
        self._problemSetsUrl = self._baseUrl + "/problem-sets"
        # the number in the website url
        self._ProblemID = {
                'b': "994805260223102976",
                'a': "994805342720868352",
                't': "994805148990160896"
                }

    def __del__(self):
        try:
            self._phantomBrowser.quit()
        except:
            pass

    def _phantomParseSoup(self, url):
        browser = self._phantomBrowser
        browser.get(url)
        # check return here
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def _parseCatatory(self, category):
        categoryUrl = "{baseurl}/{ID}/problems".format(baseurl=self._problemSetsUrl,
                      ID=self._ProblemID[category])
        logging.info('requesting page \'{}\''.format(categoryUrl))
        soup = self._phantomParseSoup(categoryUrl)
        table = soup.find('tbody')
        if table == None:
            logging.warning('requesting page \'{}\' failed, will retry (table returned None)'.format(categoryUrl))
            return None

        rows = table.find_all('tr')

        # request failed
        if len(rows) < len(config.indexes[category]):
            logging.warning('requesting page \'{}\' failed, will retry (rows length not enough)'.format(categoryUrl))
            return None

        problemList = []
        for row in rows:
            tdlist = row.find_all('td')
            link = tdlist[2].find('a')
            problemList.append({
                'index': tdlist[1].contents[0],
                'title': link.contents[0],
                'link': self._baseUrl + link['href']
            })

        return problemList

    def _parseProblem(self, url):
        soup = self._phantomParseSoup(url)
        pc = soup.find_all('div', 'ques-view')[1]
        return pc

    def download(self, indexes=config.indexes):
        """
        Download all html files
        """
        if not os.path.exists(config.html_dir):
            os.mkdir(config.html_dir)
        for c in indexes.keys():
            if len(indexes[c]) == 0:
                continue

            url_list = None
            while url_list == None:
                url_list = self._parseCatatory(c)
                if url_list == None:
                    time.sleep(5)

            for url in url_list:
                if int(url['index']) not in indexes[c]:
                    continue

                htmlfile = "{}/{}{}.html".format(config.html_dir, c, url['index'])
                if self._force is False and os.path.exists(htmlfile):
                    logging.info(htmlfile + " exists")
                    continue

                logging.info("downloading " + htmlfile)
                pc = self._parseProblem(url['link'])
                with open(htmlfile, 'w') as f:
                    f.write("{}\n{}".format(url['title'], pc))

if __name__ == "__main__":
    # setting logging
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',
                        level=logging.INFO)

    # parse arguments
    parser = argparse.ArgumentParser(description='''Python script to download
        problem content from PAT website. I will include the downloaded files
        in the repo, so this script does not need to be executed.''')
    parser.add_argument('ids', nargs='+',
                        metavar='<problem id>',
                        help='''the id of the problem, e.g. 1001 for the first
                        problem. use all for downloading all html files''')
    parser.add_argument('-f', '--force-download',
                        action='store_true',
                        help='force download html file again even if it exists')
    args = parser.parse_args()

    dlIndexes = {'a': [], 'b': [], 't': []}
    if 'all' in args.ids:
        dlIndexes = config.indexes
    else:
        for ID in args.ids:
            if not re.match(r"[abt]\d{4}", ID):
                logging.error('This id is not valid: {}'.format(ID))
                exit(0)
            category = ID[0]
            index = int(ID[1:])
            if index not in config.indexes[category]:
                logging.error('Index out of range: {}'.format(index))
                exit(0)
            dlIndexes[category].append(index)

    dl = PATDownloader(force=args.force_download)
    dl.download(dlIndexes)
