import os
import sys

def foo():
    password = input('Enter password: ')
    print('Password is ' + password)
    os.system('echo ' + password)
    
    if password == '1234':
        print('Weak password!')
    else:
        print('Password accepted')

foo()