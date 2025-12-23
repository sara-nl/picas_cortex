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
import datetime
import getpass
from picas.picas_config import PicasConfig
from picas.crypto import decrypt_password
from picas.clients import CouchDB
from picas.documents import Task


ddcal_fields = {
                'CAT': '/project/lofarvwf/Public/jdejong/picas_test/final_dd_selection.csv',
                'REPO': 'https://git.astron.nl/RD/VLBI-cwl.git',                
                'SING_BIND': '/project/lofarvwf/',
                'SIMG': '/project/lofarvwf/Public/jdejong/picas_test/test_sep_2025.sif', 
                'SUBMODS': '/project/lofarvwf/Software/lofar_facet_selfcal/submods'    
}

imaging_fields = {
                'SIMG': '/project/lofarvwf/Public/jdejong/picas_test/test_sep_2025.sif', 
                'BIND_DIR': '/project/lofarvwf/Public',
                'SOLS': 'outdir/merged.h5',
}


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
    username = getpass.getuser()
    # put dateandtime in token
    datetimestr = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S.%f")

    # Use the DB to store information for reference (paths to software etc.)
    # These will be fetched from the token and used in processing (passed to master_ddcal.sh)
    tokens = []
    n_docs = offset
    for arg in fields:
        for line in fields[arg]:
            token = {
                '_id': 'token_' + workflow + '_' + str(n_docs) + '_' + datetimestr,
                'type': 'token',
                'user': username,
                'hostname': '',
                'scrub_count': 0,
                'toil_retry': 2,
                'exit_code': '',
                'wms_jobid':'',
                'output': '',
                'workflow': workflow,
                arg: line,
            }
            if workflow=="ddcal":
                token.update(ddcal_fields)
            elif workflow=="imaging":
                token.update(imaging_fields)
            else:
                sys.exit(f"Error: unknown workflow {workflow}. Choose 'ddcal' or 'imaging'")
            tokens.append(Task(token))
            n_docs += 1

    return tokens



def loadTokens(db, workflow, tokensfile):

    # Get number of token parameters from tokensfile (in this case, folder MSDATA with observations)
    # We assume that if multiple observations need to be processed, they are in different MSDATA folders
    with open(tokensfile) as f:
        msdata = {"MSDATA": f.read().splitlines()}
        
    # get tokens
    tokens = create_tokens(workflow, msdata, offset=db.doc_count())

    # store tokens on DB
    db.save_documents(tokens)
 
def get_db():
    # create a connection to the server
    config = PicasConfig(load=True)
    db = CouchDB(
        url=config.config['host_url'],
        db=config.config['database'],
        username=config.config['username'],
        password=decrypt_password(config.config['encrypted_password']).decode())

    return db


if __name__ == '__main__':
   # Pass tokenfile and workflow to token
   workflow = sys.argv[1] # ddcal or imaging
   tokensfile = sys.argv[2]

   #Create a connection to the DB server
   db = get_db()
   #create and load the tokens to DB
   loadTokens(db, workflow, tokensfile)
