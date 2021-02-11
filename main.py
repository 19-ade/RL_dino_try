import gym_dino
import gym
import os
from PIL import Image
import numpy as np
from collections import deque
import random
import cv2
import tensorflow as tf

import warnings

warnings.filterwarnings('ignore')


tf.compat.v1.disable_eager_execution()
env=gym.make("DinoGameHeadless-v0") #here we make the headless enviroment for gym

#this is to convert the RGB pixel data (150,600,3) size to (20,50,1)
def state_process(b):

    image =cv2.cvtColor(b,cv2.COLOR_RGB2GRAY)
    image = cv2.resize(image, (50, 20))
    image=image/255.0 #normalizing the pixel values

    return image






stack_size=4
stacked_frames =deque([np.zeros((20,50), dtype=np.int) for i in range(stack_size)], maxlen=4)

# creating the input . Sequence of 4 snapshots to create a sense of motion.
def stack_frames(stacked_frames, state, is_new_episode):
    # Preprocess frame
    frame = state_process(state)
 
    if is_new_episode:
        # Clear our stacked_frames
        stacked_frames = deque([np.zeros((20,50), dtype=np.int) for i in range(stack_size)], maxlen=4)


        stacked_frames.append(frame)
        stacked_frames.append(frame)
        stacked_frames.append(frame)
        stacked_frames.append(frame)


        stacked_state = np.stack(stacked_frames, axis=2)

    else:

        stacked_frames.append(frame)


        stacked_state = np.stack(stacked_frames, axis=2)

    return stacked_state, stacked_frames

#setting the global variables 
state_size = [20, 50, 4]
action_size =2
learning_rate = 1e-4


total_episodes = 110
max_steps = 50000
batch_size = 64



max_eps=1.0
min_eps=0.0001

eps=0.1

gamma = 0.99

### MEMORY HYPERPARAMETERS
pretrain_length = batch_size   # Number of experiences stored in the Memory when initialized for the first time
memory_size = 1000000
stack_size = 4                 # Number of frames stacked



#this is the CNN architecture for processing the pixel data
class DQNetwork:
    def __init__(self, state_size, action_size, learning_rate, name='DQNetwork'):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.model= self.build_model()


    def build_model(self):
        model=tf.keras.Sequential([
            tf.keras.layers.Conv2D(32,(8,8),strides=(4,4), padding='same', input_shape=(self.state_size),activation='relu'),
            tf.keras.layers.Conv2D(64,(4,4),strides=(2,2),padding='same',activation='relu'),
            tf.keras.layers.Conv2D(64,(3,3),strides=(1,1),padding='same',activation='relu'),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(64,activation='relu'),
            tf.keras.layers.Dense(64,activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(self.action_size,activation='linear')


        ])
        Eve = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)
        model.compile(metrics=["accuracy"], loss="mse", optimizer=Eve)

        return model








DQNetwork = DQNetwork(state_size, action_size, learning_rate)
#DQNetwork.model.summary()

#saving model 
checkpoint_path="training_ckpt/cp.ckpt"
checkpoint_dir=os.path.dirname(checkpoint_path)
cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_path ,save_weights_only=True, verbose=1,save_freq=50)

#This class helps us implement the experience replay.
#add() helps adding new experiences 
#sample() generates 64(batch_size) random experiences from memory
class Remember:
    def __init__(self,max_size):
        self.memory=deque(maxlen=max_size)
    def add(self,stepinfo):
        self.memory.append(stepinfo)

    def sample(self,batchsize):
        length=len(self.memory)
        points=np.random.choice(np.arange(length), size=batchsize,replace=False)
        return [self.memory[i] for i in points]



memory=Remember(memory_size)

#this helps us handle the empty memory intially.
# we fill the initially empty memory with 64 experiences generated by action which are
#in  turn generated randomly
for i in range(pretrain_length):
    if i==0:
        state=env.reset()

        state, stacked_frames = stack_frames(stacked_frames, state, True)
    action=random.randint(0,1)
    state_next,reward, done,_=env.step(action)

    state_next, stacked_frames = stack_frames(stacked_frames, state_next, False)
    if done:
        state_next=np.zeros(state_size)
        memory.add((state,action,reward,state_next,done))
        state = env.reset()

        state, stacked_frames = stack_frames(stacked_frames, state, True)
    else:

        memory.add((state, action, reward, state_next,done))
        state=state_next

'''def epsilon_value(total_episodes,episode):
    f=(total_episodes-episode)/2
    r=np.max(f,0)
    eps=(max_eps-min_eps)*r + min_eps
    return eps'''

# generating action . (Exploitation and explortion conundrum)
def get_action(state):




    if (np.random.rand() <= eps):
        action=np.random.randint(0,1)
    else:
        Q=DQNetwork.model.predict(state.reshape(1,*state.shape))
        action=np.argmax(Q) #since action is 0 or 1 and we perform the acion corresponding to max Q value we can cheat a little and just use argmax()


    return action,eps

total_rewards=[]

#This is where we finally train the agent
#please note that unlike other gym enviroments theres no time limit 
#the aim is to survive as long as possible 
#for this purpose max-steps is used 
#its set to an unrealistic value(50000) to hopefully mimic this situation

def training(stacked_frames):
    DQNetwork.model.load_weights(filepath=checkpoint_path)#load the pre-loaded weights

    for episode in range(total_episodes):    #total training episodes
        step_taken = 0
        episode_rewards = []

        state = env.reset()
        state, stacked_frames = stack_frames(stacked_frames, state, True)
        while step_taken < max_steps:
            step_taken = step_taken + 1
            action = get_action(state)
            next_state, reward, done, _ = env.step(action)
            episode_rewards.append(reward)
            if done:
                next_state = np.zeros((20, 50, 3), dtype=np.float32)

                next_state, stacked_frames = stack_frames(stacked_frames, next_state, False)
                step_taken = max_steps
                total_reward = np.sum(episode_rewards)
                total_rewards.append(total_reward)
                memory.add((state, action, reward, next_state, done))#adding experience to memory
                print("episode=", episode, "    ", "reward=", total_reward, " ", "episode_reward=", episode_rewards)


            else:
                next_state, stacked_frames = stack_frames(stacked_frames, next_state, False)
                memory.add((state, action, reward, next_state, done))# adding experience to memory
                state = next_state
            
            
            
            batch = memory.sample(batch_size)#generating 64 rando samples
            states_mb = np.array([each[0] for each in batch], ndmin=3)

            rewards_mb = np.array([each[2] for each in batch])
            next_states_mb = np.array([each[3] for each in batch], ndmin=3)
            dones_mb = np.array([each[4] for each in batch])
            targets_mb = np.empty(shape=(64, 2))

            target_Qs_batch = []
            Q_s_dash = DQNetwork.model.predict(next_states_mb)
            # print(Q_s_dash)
            for i in range(0, len(batch)):
                terminal = dones_mb[i]

                # If we are in a terminal state equating to reward 
                if terminal:
                    target = rewards_mb[i]
                    target_Qs_batch.append(target)

                else:
                    target = rewards_mb[i] + gamma * np.max(Q_s_dash[i])# Bellman optimality equation
                    target_Qs_batch.append(target)

                targets_mb[i] = np.array(target_Qs_batch[i])#the target Q values 

            DQNetwork.model.fit(states_mb, targets_mb, callbacks=[cp_callback])#training model


'''
training(stacked_frames)
DQNetwork.model.save("vidw_model.h5")

plt.plot(total_rewards)
plt.show()

'''
