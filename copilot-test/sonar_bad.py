import os
import sys

import getpass
import hashlib

def foo():
    password = getpass.getpass('Enter password: ')
    # Do not print or log the password
    # Example: check password hash (replace with real user DB in production)
    weak_password_hash = hashlib.sha256('1234'.encode()).hexdigest()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash == weak_password_hash:
        print('Weak password!')
    else:
        print('Password accepted')

foo()