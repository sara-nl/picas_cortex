#!/usr/bin/env python
"""
@helpdesk: SURF helpdesk <helpdesk@surf.nl>

Push tokens to the PiCaS database for PoC lofarvwf/CORTEX

Usage:
    python push_tokens.py [tokensfile] [inputfile] [workflow]


Description:
   - Connects to PiCaS server
   - Creates tokens for <workflow>: "ddcal" or "imaging"
   - Saves the tokens to the database
"""
import sys
import time
import getpass
import os
from picas.clients import CouchDB
import picasconfig
from picas.documents import Task


def create_tokens(workflow, fields: dict, offset: int = 0) -> list:
    """
    Create the tokens as a list of Task documents.

    The fields parameter is a dictionary where keys are field names and values are
    lists of input values. For every 'input' value a unique id is assigned and the
    corresponding input value is used to create a token.

    :param fields: A dictionary where keys are field names and values are lists of input values.
    :param offset: An integer offset to start numbering the token IDs from (default is 0).
     This is useful if you want to create tokens in multiple batches and ensure unique IDs.
    :return: A list of Task documents representing the tokens.
    """

    # Get info to put in tokens
    # username
    username =  getpass.getuser()

    tokens = []
    n_docs = offset
    for arg in fields:
        for line in fields[arg]:
            token = {
                '_id': 'token_' + str(n_docs),
                'type': 'token',
                'user': username,
                'hostname': '',
                'scrub_count': 0,
                'toil_retry': 2,
                'repo': 'https://git.astron.nl/RD/VLBI-cwl.git',
                'cat': '/project/lofarvwf/Public/jdejong/picas_test/msdata',
                'exit_code': '',
                'wms_jobid':'',
                'workflow': workflow,
                arg: line,
            }
            tokens.append(Task(token))
            n_docs += 1

    return tokens



def loadTokens(db, tokensfile):

    # Get number of token parameters from tokensfile
    with open(tokensfile) as f:
        msdata = {"msdata": f.read().splitlines()}
    workflow = "ddcal"
        
    # get tokens
    tokens = create_tokens(workflow, msdata, offset=db.doc_count())

    # store tokens on DB
    db.save_documents(tokens)
 
def get_db():
    # create a connection to the server
    db = CouchDB(
        url=picasconfig.PICAS_HOST_URL,
        db=picasconfig.PICAS_DATABASE,
        username=picasconfig.PICAS_USERNAME,
        password=picasconfig.PICAS_PASSWORD)

    return db


if __name__ == '__main__':
   # Pass tokenfile and inputfile to token
   tokensfile = sys.argv[1]
   #Create a connection to the DB server
   db = get_db()
   #create and load the tokens to DB
   loadTokens(db, tokensfile)
