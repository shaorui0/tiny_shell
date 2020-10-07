import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from shell import Shell

if __name__ == "__main__":
    shell = Shell()
    shell.loop()