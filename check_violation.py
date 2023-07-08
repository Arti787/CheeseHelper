import random
import string
import time

def random_string(length):
    letters = string.ascii_letters + string.digits + string.punctuation + string.whitespace
    return ''.join(random.choice(letters) for i in range(length))

print(random_string(random.randint(15, 25)))
