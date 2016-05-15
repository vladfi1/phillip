act_every = 5
fps = 60 // act_every
experience_time = 60
experience_length = fps * experience_time

# reward computation
tdN = 5

reward_halflife = 2.0 # seconds
discount = 0.5 ** ( 1.0 / (fps*reward_halflife) )
