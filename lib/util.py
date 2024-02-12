import time

def get_unix_timestamp() -> int:
   return time.mktime(time.gmtime())