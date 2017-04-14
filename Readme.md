# The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

Check Vlad's repository for original Readme

## Notes
- python3 runner.py --tag
- python3 launcher.py saves/RecurrentActorCritic_entropy_scale_0.01_learning_rate_1e-05_action_type_custom_act_every_3_char_falcon_enemies_cpu/ --init
- python3 launcher.py saves/RecurrentActorCritic_entropy_scale_0.01_learning_rate_1e-05_action_type_custom_act_every_3_char_falcon_enemies_cpu/ --trainer [node #]

- tensorboard --logdir=logs --port=random#
- sq | grep vlad
- scontrol show job [job #]
- scancel [job #]
- ./scancel RecurrentActorCritic
- scancel -u vladfi1
