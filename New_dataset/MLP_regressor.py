import os
import time
import datetime
from contextlib import contextmanager
import random
import pandas as pd
import numpy as np

from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.externals import joblib

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


@contextmanager
def measure_time(label):
    """
    Context manager to measure time of computation.
    """
    start = time.time()
    yield
    end = time.time()
    print('Duration of [{}]: {}'.format(label, datetime.timedelta(seconds=end-start)))


def load_data(path, to_split=True,delimiter=','):
    """
    Load the csv file and returns (X,y).
    """
    df = pd.read_csv(path, delimiter=delimiter)
    y = df['PlayerA Win'].values.squeeze()

    # # Take all numerical features
    # df = df.iloc[:,8:]
    # df = df.drop(columns=['PlayerA Win'])
    # selected_features = df.columns

    # Only take some
    selected_features = ['WinA_%', 'PlayerA_age', 'PlayerA_rank', 'PlayerA_rank_points',
                        'WinB_%', 'PlayerB_age', 'PlayerB_rank', 'PlayerB_rank_points']
    df = df[selected_features]
    X = df.values.squeeze()
    
    if to_split:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        return X_train, X_test, y_train, y_test, selected_features
    else:
        return X, y, selected_features


def train(path, testFeatureImportance=False, to_split=True):
    """
    Train th model.
    """
    model = None
    filename = "MLP.pkl"
    
    # Load the training (and testing) set(s)
    if to_split:
        X_train, X_test, y_train, y_test, train_features = load_data(path, to_split=to_split)
    else:
        X, y, train_features = load_data(path, to_split=to_split)

    # Get the most important features
    print("Training... getting most important features")
    if testFeatureImportance:
        ntry = 10
    else:
        ntry = 1
    feature_importance_total = np.zeros((train_features.shape[0],1))
    for n in range(ntry):
        with measure_time('Training...getting most important features'):
            print("N = ", n)
            model = MLPClassifier()
            model.fit(X_train, y_train)
            if not testFeatureImportance:
                joblib.dump(model, filename) 
        
        feature_importance_total = np.add(feature_importance_total, np.array(model.feature_importances_).reshape(train_features.shape[0],1))

    if testFeatureImportance:
        feature_importances = pd.DataFrame(feature_importance_total,
                                            index = train_features,
                                            columns=['importance'])

        print("Most important features")
        feature_importances['importance'] = feature_importances['importance'] / ntry
        print(feature_importances[:50].sort_values('importance',ascending=False))
        feature_importances[:50].to_csv("feature_importance.csv")

    y_pred = model.predict(X_train)
    print("Training set accuracy: {}".format(accuracy_score(y_train, y_pred)))
    print("=================================================================")
    
    y_pred = model.predict(X_test)
    print("Test set accuracy: {}".format(accuracy_score(y_test, y_pred)))
    print("=================================================================")


def tune_hyperparameter(path):
    """
    Get the best hyperparameters.
    """
    # Load the training set
    X, y, _ = load_data(path, to_split=False)
        
    # Create the random grid
    random_grid = {'hidden_layer_sizes': [(50,50,50), (50,100,50), (100,)],
                    'activation': ['tanh', 'relu'],
                    'solver': ['sgd', 'adam'],
                    'alpha': [0.0001, 0.05],
                    'learning_rate': ['constant','adaptive']}
    
    # Use the random grid to search for best hyperparameters
    # First create the base model to tune
    mlp = MLPClassifier(max_iter=200)
    # Random search of parameters, using 3 fold cross validation, 
    # search across 100 different combinations, and use all available cores
    mlp_random = RandomizedSearchCV(estimator = mlp,
                                   param_distributions = random_grid,
                                   n_iter = 100,
                                   cv = 3,
                                   verbose=2,
                                   random_state=42,
                                   n_jobs = -1)
    # Fit the random search model
    mlp_random.fit(X, y)

    print("Best parameters", mlp_random.best_params_)
    # Best parameters {'n_estimators': 1400, 'min_samples_split': 2, 'min_samples_leaf': 1, 'max_features': 'auto', 'max_depth': 40, 'bootstrap': False}


if __name__ == "__main__":
    path = 'new_stats_data.csv'

    #tune_hyperparameter(path)
    train(path, testFeatureImportance=False, to_split=True)