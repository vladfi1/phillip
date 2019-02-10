from phillip.env.ssbm_env import SSBMEnv
import time
import argparse

parser = argparse.ArgumentParser()
SSBMEnv.update_parser(parser)

args = parser.parse_args()

env = SSBMEnv(**args.__dict__)
#cpu1=9, cpu2=9

time.sleep(30)

env.close()

