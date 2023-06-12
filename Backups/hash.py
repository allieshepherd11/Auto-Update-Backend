import hashlib


print(hashlib.sha256('asdf'.encode()).hexdigest())
hp = 'f0e4c2f76c58916ec258f246851bea091d14d4247a2fc3e18694461b1816e13b'

userpass = input('Enter password: ')
if hashlib.sha256(userpass.encode()).hexdigest() == hp:
    print('Nice')
else:
    print('Try again')