'''
Main python file for the Ant Colony Optimization algorithm
'''

import os
import argparse
import json
from colony_system import ColonySystem


def load_config(cfg_path):
    if cfg_path is None or not os.path.exists(cfg_path):
        raise ValueError('Config file not found {}'.format(cfg_path))

    with open(os.path.realpath(cfg_path)) as data_file:
        cfg_json = json.load(data_file)

    return cfg_json


def launch(cfg_path):
    print '[INFO]', 'Starting ACO...'
    print '[INFO]', 'Loading config'

    json_cfg = load_config(cfg_path)
    print '[DEBUG]', json_cfg

    colony = ColonySystem(json_cfg)
    colony.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=False, type=str)
    opts = parser.parse_args()

    launch(opts.config)
