# Spaceship-Titanic
Predict which passengers are transported to an alternate dimension.

"While rounding Alpha Centauri en route to its first destination—the torrid 55 Cancri E—the unwary Spaceship Titanic collided with a spacetime anomaly hidden within a dust cloud. Sadly, it met a similar fate as its namesake from 1000 years before. Though the ship stayed intact, almost half of the passengers were transported to an alternate dimension!
To help rescue crews and retrieve the lost passengers, you are challenged to predict which passengers were transported by the anomaly using records recovered from the spaceship’s damaged computer system."

In this classification problem, first I performed some data preparation and then used three algorithms. Catboost by feeding categorical features directly into the model, XGBoost and PyTorch (both with Softmax and Sigmoid activation functions). 

Softmax activation function performed best among all models even better than the ensemble of Catboost, XGBoost and Sigmoid PyTorch.

Softmax PyTorch accuracy_score was 0.80640 and ensemble score was 0.80453.

In this project I figured out features built from the target column, like age of transported passengers or transported ratio of different class of customers, can cause high overfitting to train dataset and removed them.
