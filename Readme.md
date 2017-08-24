# The Phillip AI
An SSBM player based on Deep Reinforcement Learning.

Check Vlad's repository for original Readme

## Notes
### Grid Search
To run the gridsearch over 50 random samples from the grid for RDQN, use:

`python gridsearch.py --model RecurrentDQN --num_samples 50`

If you just want to see how it will call runner.py without actually executing runner.py, use:

`python gridsearch.py --model RecurrentDQN --num_samples 50 --dry_run`

After you call `gridsearch.py`, you can run `batcher.py`:

`python batcher.py`

which should launch the jobs one by one at 4 hour intervals.

### Launch
- python3 runner.py --tag
- python3 launcher.py saves/RecurrentActorCritic_entropy_scale_0.01_learning_rate_1e-05_action_type_custom_act_every_3_char_falcon_enemies_cpu/ --init
- python3 launcher.py saves/RecurrentActorCritic_entropy_scale_0.01_learning_rate_1e-05_action_type_custom_act_every_3_char_falcon_enemies_cpu/ --trainer [node #]																																																																																																																																																																																																																																																																																																																									
