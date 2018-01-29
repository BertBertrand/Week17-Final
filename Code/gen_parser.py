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
import os.path
import glob
import sys

import state_machine
import x12_parser
import edi_handler

import azure.storage.blob as azureblob

class gen_parser:
    def __init__(self):
        self.end_last_edi = 0
        self.curr_anchor = 0
        self.start_curr_poten_doc = 0
        self.handled_to = 0
        #self.edi_handler_class = edi_handler.GenericEDIHandler
        self.edi_handler_class = edi_handler.Translator
        self.non_edi_handler_class = edi_handler.NonEDIHandler

    def searching_header(self, cargo):
        infile, tag = cargo
        while 1:
            self.start_curr_poten_doc = infile.tell()
            poten_tag = infile.read(3)
            if poten_tag == "ISA":
                return (self.x12.header_seg, (infile, poten_tag))
            #add checks for other header types here like UNA, UNB
            elif len(poten_tag) < 3:
                return self.eof, infile
            else:
                infile.seek(-2, 1)

    def eof(self, infile):
        curr_pos = infile.tell()
        if self.handled_to < curr_pos:
            non_edi_handler = self.non_edi_handler_class()
            infile.seek(self.handled_to)
            read_len = curr_pos - self.handled_to
            data = infile.read(read_len)
            non_edi_handler.non_edi_data(data, self.handled_to, curr_pos)
            infile.seek(curr_pos)
    def error(self, infile):
        pass

    def run(self, infile):
        m = state_machine.StateMachine()
        m.add_state(self.searching_header)
        m.add_state(self.error, end_state=1)
        m.add_state(self.eof, end_state=1)
        m.set_start(self.searching_header)
        #x12 parser
        self.x12 = x12_parser.x12_parser(self)
        self.x12.add_transitions(m)
        #add new parsers here
        m.run((infile, ''))

if __name__ == "__main__":

    #######################################################
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--filepath',         required=True, help='The path to the EDI file to process.')
    parser.add_argument('--storageaccount',   required=True, help='The name the Azure Storage account that owns the blob storage container to which to upload results.')
    parser.add_argument('--storagecontainer', required=True, help='The Azure Blob storage container to which to upload results.')
    parser.add_argument('--sastoken',         required=True, help='The SAS token providing write access to the Storage container.')
    args = parser.parse_args()

    #######################################################
    # calculate output filename
    input_filename, input_fileextension = os.path.splitext(args.filepath)
    output_filename = input_filename
    g = gen_parser()
    g.edi_handler_class.xml_prefix = output_filename

    #######################################################
    # Run the X12 -> XML conversion
    g.run(open(args.filepath, 'r'))

    #######################################################
    # Upload the result file to the storage account

    # Create a blob client
    blob_client = azureblob.BlockBlobService(account_name=args.storageaccount,sas_token=args.sastoken)

    # Get a list of output files to upload
    globarg = input_filename + '*.xml'
    result_files = glob.glob(globarg)

    # Upload each file to the blob
    for result_file in result_files:
        # Get the full path to the output file
        result_file_path = os.path.dirname(os.path.realpath(result_file))
        result_filename = os.path.basename(os.path.realpath(result_file))

        # Upload the file to the output container blob
        print('\nFrom path: {}\n    Uploading file: {}\n    To container [{}]...'.format(result_file_path,result_filename, args.storagecontainer))
        blob_client.create_blob_from_path(args.storagecontainer, result_filename, result_file)
