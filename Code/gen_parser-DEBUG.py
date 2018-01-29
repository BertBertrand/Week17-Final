#!/usr/bin/env python
#
# https://creativecommons.org/licenses/by-sa/4.0/
# https://creativecommons.org/licenses/by-sa/4.0/legalcode
#
################################################################################
# Based on an article from
#   Jeremy Jones
#   Processing EDI Documents into XML with Python
#   http://www.devx.com/enterprise/Article/26854
#
# Used under permission for single use, non-commercial:
#   You may use one of our articles for a non-commercial project (for example, a school project) provided that QuinStreet's copyright clause accompanies the article:
#
#   Reproduced with permission.
#   Copyright 1999-2018 QuinStreet, Inc. All rights reserved.
#
# Available at http://www.devx.com/licensing
################################################################################

import argparse
import os
import glob
import sys

if __name__ == "__main__":

    #######################################################
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--filepath',         required=True, help='The path to the EDI file to process.')
    parser.add_argument('--storageaccount',   required=True, help='The name the Azure Storage account that owns the blob storage container to which to upload results.')
    parser.add_argument('--storagecontainer', required=True, help='The Azure Blob storage container to which to upload results.')
    parser.add_argument('--sastoken',         required=True, help='The SAS token providing write access to the Storage container.')
    args = parser.parse_args()

    cwd = os.getcwd()

    print('cwd = ' + cwd)

    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        print('f = ' + f)

    print('xml file location: ')
    os.system('find / -name x12_schema.xml -print')
