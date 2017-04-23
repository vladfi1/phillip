# The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

Check Vlad's repository for original Readme

## Notes
- python3 runner.py --tag
- python3 launcher.py saves/RecurrentActorCritic_entropy_scale_0.01_learning_rate_1e-05_action_type_custom_act_every_3_char_falcon_enemies_cpu/ --init
- python3 launcher.py saves/RecurrentActorCritic_entropy_scale_0.01_learning_rate_1e-05_action_type_custom_act_every_3_char_falcon_enemies_cpu/ --trainer [node #]

- tensorboard --logdir=logs --port=random#
- sq | grep Vlad
- scontrol show job [job #]
- scancel [job #]
- ./scancel.sh RecurrentActorCritic
- scancel -u vladfi1
- squeue -u vladfi1 -o %j

## TODO
- Edit RDQN to have same architecture as rac (2 Q layers, followed by GRU cell)
- Set reward_halflife to 2 and make sure runner works
- Train 80 agents with RDQN (keep temperature the same)
- Train 80 agents with RAC (lower entropy to normal (not recurrent))
(Vlad set initial hidden state of GRU cell to 0, it was originally chosen by agent, now we have options of empty state, let agent decide, and make it learned parameter)																																																																																																																																																																																																																																																																																																																										