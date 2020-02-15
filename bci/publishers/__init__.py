import os
for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    module = module[:-3]
    __import__(f'bci.publishers.{module}', locals(), globals(), ['publish'])
del module
