---
layout: default
title: Proposal
---
## Summary of the Project
For our project, we will have a Minecraft agent with a bow and use reinforcement learning to teach it to shoot targets at a distance, which may be in motion. This will require the agent to lead targets and account for arrow drop. Our input will be an observation from Malmo indicating the target’s location relative to the agent’s position and rotation. Our output will be the actions that the agent takes in that situation and the result of the actions taken in the given situation.
## AI/ML Algorithms
We will use reinforcement learning with neural function approximator so that the AI can take in information about the target’s location and improve its aim based on how close the arrow lands to the target.
## Evaluation Plan
The main metric we will use to measure how successful our agent is its percentage of successful hits against randomly placed enemies over a set number of shots. Our baseline will be the accuracy rate of a human with a bow.  If the AI meets expectations, it should exceed regular human accuracy by a notable margin.
Sanity cases can include shooting a very close range target or a non-moving target at range. We can visualize how well our algorithm is working by running it on a Minecraft agent, as it will be very obvious whether or not it is intelligently aiming at the target. Our moonshot case is having our agent fight the Ender Dragon enemy, which is constantly moving in 3d space at a long distance away from the player.
