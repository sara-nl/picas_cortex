'''
@helpdesk: SURFsara helpdesk <helpdesk@surfsara.nl>

usage: python pilot.py [workflow]			
description:                                                                  	
	Connect to PiCaS server          	
	Get the next token in todo View of [workflow]			
	Fetch the token parameters, e.g. input value 					
	Run main job, master_[workflow].sh		
	When done, return the exit code to the token
	Attach the logs to the token							
'''

#python imports
import os
import sys
import push_tokens
#picas imports
from picas.picas_config import PicasConfig
from picas.crypto import decrypt_password
from picas.actors import RunActor
from picas.clients import CouchDB
from picas.iterators import TaskViewIterator
from picas.modifiers import BasicTokenModifier
from picas.executers import execute

class ExampleActor(RunActor):
    def __init__(self, db, modifier, view="todo", **viewargs):
        super(ExampleActor, self).__init__(db, view=view, **viewargs)
        self.iterator = TaskViewIterator(db, view, **viewargs)
        self.modifier = modifier
        self.client = db


    def process_task(self, token):
	    # Print token information
        print("-----------------------")
        print("Working on token: " +token['_id'])
        for key, value in token.doc.items():
            print(key, value)
        print("-----------------------")


        # Start running the main job
        workflow=str(token['workflow'])
        if workflow=="ddcal":
            command = ["/usr/bin/time", f"./master_{workflow}.sh",
                    token['MSDATA'], token['SING_BIND'], token['SIMG'], token['CAT'], token['REPO'], token['SUBMODS']]
            # Put location of output in token (created in master_ddcal.sh script)
            token['output'] = os.getcwd() + "/outdir"        
        elif workflow=="imaging":
            command = ["/usr/bin/time", f"./master_{workflow}.sh",
                    token['MSDATA'], token['BIND_DIR'], token['SIMG'], token['SOLS']]
            # Put location of output in token (created in master_imaging.sh script)
            token['output'] = os.getcwd() + "/imaging_output" 

        print(command)        
        out = execute(command)
        self.subprocess = out[0]

        # Get the job exit code and done in the token
        token['exit_code'] = out[1]           
        token = self.modifier.close(token)

        # write the logs
        logsout = f"logs_{token['_id']}.out"
        logserr = f"logs_{token['_id']}.err"

        with open(logsout, 'w') as f:
            f.write(out[2].decode('utf-8'))
        with open(logserr, 'w') as f:
            f.write(out[3].decode('utf-8'))

        # Attach logs in token
        try:
            log_handle = open(logsout, 'rb')
            token.put_attachment(logsout, log_handle.read())

            log_handle = open(logserr, 'rb')
            token.put_attachment(logserr, log_handle.read())
            # Attach used input.json in token
            if token['exit_code']==0 and token['workflow']=='ddcal':
               filename = "input.json"
               f = open(filename, 'rb')
               token.put_attachment(filename, f.read())
               f.close()

        except:
           pass

        # if "ddcal" token succeeded, create "imaging" token
        if token["exit_code"]==0 and workflow=="ddcal":

            # Create tokensfile
            tokensfile = "tokensfile.txt"
            with open(tokensfile, "w") as f:
                f.write(token["MSDATA"])

            # Pass outdir from "ddcal" job to new "imaging" token
            push_tokens.imaging_fields['SOLS'] = token["output"] + "/merged.h5"
            push_tokens.loadTokens(self.db, "imaging", tokensfile)        


def main():

    if len(sys.argv)!=2:
       sys.exit("Specify workflow")
    else:
       workflow = sys.argv[1]

    # setup connection to DB server
    config = PicasConfig(load=True)
    client = CouchDB(
        url=config.config['host_url'],
        db=config.config['database'],
        username=config.config['username'],
        password=decrypt_password(config.config['encrypted_password']).decode())

    # Create token modifier
    modifier = BasicTokenModifier()

    # Create actor
    actor = ExampleActor(client, modifier, "todo", design_doc=workflow)    
    # Start work!
    print("Connected to the database %s sucessfully. Now starting work..." %(config.config['database']))

    # Exit pilot job, if runtime is larger than maxtime, after processing at least one token
    maxtime = 4*24*3600  # 4 days  
    actor.run(max_total_time=maxtime)

if __name__ == '__main__':
    main()

