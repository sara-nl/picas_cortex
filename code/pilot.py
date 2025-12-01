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
import time
import sys
import json
import picasconfig
#picas imports
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
        elif workflow=="imaging":
            command = ["/usr/bin/time", f"./master_{workflow}.sh",
                    token['MSDATA'], token['BIND_DIR'], token['SIMG'], token['SOLS']]

        print(command)
        
        out = execute(command)

        logsout = f"logs_{token['_id']}.out"
        logserr = f"logs_{token['_id']}.err"

        # write the logs
        with open(logsout, 'w') as f:
            f.write(out[2].decode('utf-8'))
        with open(logserr, 'w') as f:
            f.write(out[3].decode('utf-8'))

        self.subprocess = out[0]

        # Get the job exit code and done in the token
        token['exit_code'] = out[1]           
        token = self.modifier.close(token)

        # Attach logs in token
        curdate = time.strftime("%d/%m/%Y_%H:%M:%S_")
        try:
            log_handle = open(logsout, 'rb')
            token.put_attachment(logsout, log_handle.read())

            log_handle = open(logserr, 'rb')
            token.put_attachment(logserr, log_handle.read())
            # Attach used input.json in token
            if token['exit_code']==0 and token['workflow']=='ddcal':
               filename = ""
               f = open("input.json", 'rb')
               token.put_attachment(filename, f.read())
               f.close()

        except:
           pass

def main():

    if len(sys.argv)!=2:
       sys.exit("Specify workflow")
    else:
       workflow = sys.argv[1]

    # setup connection to db
    db_name = picasconfig.PICAS_DATABASE
    client = CouchDB(url=picasconfig.PICAS_HOST_URL, db=picasconfig.PICAS_DATABASE, username=picasconfig.PICAS_USERNAME, password=picasconfig.PICAS_PASSWORD)
    # Create token modifier
    modifier = BasicTokenModifier()

    # Create actor
    actor = ExampleActor(client, modifier, "todo", design_doc=workflow)    
    # Start work!
    print("Connected to the database %s sucessfully. Now starting work..." %(picasconfig.PICAS_DATABASE))

    # Exit pilot job, if runtime is larger than maxtime, after processing at least one token
    maxtime = 4*24*3600  # 4 days  
    actor.run(max_total_time=maxtime)

if __name__ == '__main__':
    main()

