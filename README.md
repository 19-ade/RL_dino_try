# RL_dino_try
An RL agent attempts to play the google chrome dino game. I have created a gym enviroment for the same and have implemented the DQN model to tain the agent . The gym 
enviroment can be found [here](https://github.com/19-ade/gym-dino-game)


## Setting up the enviroment
------------------------------------------------------------------------
**Please make sure you have Google chrome installed*


1. Clone the RL_dino_try repo
```
git clone https://github.com/19-ade/RL_dino_try.git
```

2.Clone the gym-dino-game(gym enviroment for the given code)
```
git clone https://github.com/19-ade/gym-dino-game.git
```
3.Install the gym enviroment :
```cd``` your way to the gym-dino-game folder on your system . 
```
cd /path/to/gym-dino-game
pip install -e .

```

*If you are using an enviroment to open RL_dino_try (Anaconda etc..) please make sure you follow the above steps inside a terminal of the enviroment*

4.NOw that the enviroment is installed we come back to RL_dino_try . Run the *requirements.py* script in the repo . This will install all the necessary libraries 
for our program.
```
cd /path/to/RL_dino_try
python requirements.py

```

5. Now we will run the *test.py* script. It just creates the dino enviroment .This is to make sure that everything is working fine.

```
python test.py
```









