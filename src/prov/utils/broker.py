import os

broker = {'host': os.environ['MHOST'] if 'MHOST' in os.environ else "localhost",
          'user': os.environ['MUSER'] if 'MUSER' in os.environ else "user",
          'pass': os.environ['MKEY'] if 'MKEY' in os.environ else "password"}
