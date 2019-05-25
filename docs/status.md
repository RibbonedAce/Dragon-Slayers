---
layout: default
title:  Status
---

<iframe width="720" height="480" src="https://www.youtube.com/embed/K_xamKkgG7c" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## Project Summary
For our project, we have a Minecraft agent with a bow and use reinforcement learning to teach it to shoot targets at a distance. Our input is an observation from Malmo indicating the target’s location/distance relative to the agent’s position and rotation. Our output is the actions that the agent takes in that situation (i.e. changes in pitch and yaw) and the result of the actions taken in the given situation. By the time of our status report, we have implemented an agent that can accurately shoot a non-moving target by adjusting both its horizontal and vertical aim for targets on the same elevation as our agent and even targets elevated above our agent.

## Approach
Our agent learns how to shoot accurately at a bow using linear regression. Specifically, our agent uses linear regression for the separate axes of aiming that can be done in Minecraft. One regression method is used for horizontal aiming and another is used for vertical aiming, each method using some dimensions of features taken from the game to estimate the angle needed to aim to hit the target with the given features in the same dimensions.

For vertical aiming, our agent uses regression with using the features of distance from the target and difference in elevation from the target (if the target is higher than the shooter, the elevation is positive). Because of the funciontality if physics in Minecraft, we decided to use polynomial combinations of these features as the dimensions of regression. Our output of this regression is the vertical angle needed to aim to hit a target at the given distance and elevation. The following equation is the regression equation:<br>
$$angle = a + b\*distance + c\*elevation + d\*distance^2 + e\*distance\*elevation + f\*elevation^2$$

## Evaluation

## Remaining Goals and Challenges
Currently, our agent could essentially only fight an army of scarecrows, albeit scarecrows of various distances and elevations. Our remaining goals include the addition of movement to our target. This involves taking the velocity as input and our agent predicting where the target will move in order to lead the shot. This however can prove quite challenging as well since movement is not limited to one dimension. Similarly to the previous implementation of aiming, we must think about velocity in two different dimensions (maybe even three for flying enemies!).

## Resources Used
- [Matplotlib](https://matplotlib.org/)
- [NumPy](https://www.numpy.org/)
- [SciKit-Learn](https://scikit-learn.org/stable/)
  - Linear Regression [~](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)
  - Polynomial Features [~](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.PolynomialFeatures.html)
