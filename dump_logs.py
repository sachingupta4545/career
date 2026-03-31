import os
import subprocess

with open('err.txt', 'w') as f:
    subprocess.run(['docker', 'compose', 'logs', 'api', '--tail', '50'], stdout=f, stderr=subprocess.STDOUT)
