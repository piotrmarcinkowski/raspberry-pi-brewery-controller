import os

RUN_ON_RASPBERRY = True
if 'RUN_ON_RASPBERRY' in os.environ and os.environ['RUN_ON_RASPBERRY'] == '0':
    RUN_ON_RASPBERRY = False
