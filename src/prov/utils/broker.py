from os import environ

broker = {'host': environ['MHOST'] if 'MHOST' in environ else "localhost",
          'user': environ['MUSER'] if 'MUSER' in environ else "user",
          'queue': environ['MQUEUE'] if 'MQUEUE' in environ else "provenance.inbox",
          'pass': environ['MKEY'] if 'MKEY' in environ else "password"}
