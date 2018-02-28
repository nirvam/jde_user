#!/usr/bin/env python
# -*- coding: utf-8 -*-

# "THE BEER-WARE LICENSE" (Revision 42):
# <marvin.beeblebrox@gmail.com > wrote this script.
# As long as you retain this notice you can do whatever you want with this stuff.
# If we meet some day, and you think this stuff is worth it, you can buy me a beer in return.
#
# Copyright(c) 2018 Marvin Zhang
#

'''jde_user.py
Grab current online user count from Server Manager Console.
Designed to work with Zabbix or as a standalone application.

Required Python libraries:
- bs4
- requests
'''


import requests
import sys
from bs4 import BeautifulSoup
from time import localtime, strftime
import argparse
import time


class user_metrics():
    def __init__(self, URL, USERNAME, PASSWORD):
        try:
            self._metrics = self._get_metrics(URL, USERNAME, PASSWORD)
        except Exception as e:
            print('Failed during connection!\n{}'.format(e))
            self._metrics = None

    def _get_metrics(self, URL, USERNAME, PASSWORD):
        # connect to SM console and get session metrics from Disable Logins page
        with requests.Session() as s:
            # login
            s.get(URL + '/home')
            s.post(URL + '/j_security_check',
                   data={'j_username': USERNAME, 'j_password': PASSWORD})
            # fetch user session metrics
            r = s.get(URL + '/target?targetType=webserver&action=disableLogins')
            # logout
            s.get(URL + '/logon?action=logout')

        # deal with metrics and return dict
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find(id='webInstances').find('tbody')
        metrics = {}
        for row in table.find_all('tr'):
            inst_name = row.find('a').get_text()
            # the third column to the right should be "Online User Count"
            user_count = int(row.find_all('td')[-3].get_text())
            # deal with cluster -- they have same inst_name, so should calc sum
            metrics[inst_name] = metrics.get(inst_name, 0) + user_count
        return metrics

    def get_instances(self):
        return self._metrics.keys()

    def get_user(self, instance):
        try:
            return self._metrics[instance]
        except KeyError:
            print('The instance specified does not exists!')
            return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='jde_user.py')
    parser.add_argument('URL', help='Url for SM console. Ends with "/manage".')
    parser.add_argument(
        'USERNAME',  help='SM console username. Usually should be "jde_admin".')
    parser.add_argument('PASSWORD',  help='Password of the SM console user.')
    parser.add_argument('-t', '--timestamp',
                        action='store_true', help='Print current timestamp.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--list', action='store_true',
                       help='List all available instances.')
    group.add_argument('-a', '--all', action='store_true',
                       help='List all instances and user counts as a table. (default action if no mode specified)')
    group.add_argument('-i', '--instance',
                       help='Instance of which needs be queried.')
    args = parser.parse_args()

    metr = user_metrics(args.URL, args.USERNAME, args.PASSWORD)

    if args.timestamp:
        print(time.strftime('%Y-%m-%d %H:%M:%S'))
    if args.list:
        print('\n'.join(metr.get_instances()))
    elif args.instance:
        print(metr.get_user(args.instance))
    else:
        for i in metr.get_instances():
            print('\t'.join([i, str(metr.get_user(i))]))
