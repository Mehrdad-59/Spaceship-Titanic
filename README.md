# Spaceship-Titanic
Predict which passengers are transported to an alternate dimension.

In this classification problem, first I performed some data preparation and then used three algorithms. Catboost by feeding categorical features directly into model, XGBoost and PyTorch both with Softmax and Sigmoid activation functions. 

Softmax activation function performed best among all models even better than the ensemble of Catboost, XGBoost and Sigmoid PyTorch.

Softmax PyTorch accuracy_score was 0.80640 and ensemble score was 0.80453.

In this project I figured out features built from the target colunm, like age of transported passengers or transported ratio of different class of customers, can cause high overfitting to train dataset and removed them.
