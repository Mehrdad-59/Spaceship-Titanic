# -*- coding: utf-8 -*-
"""Spaceship Titanic _CatBoost_0.79985.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12Nceo7mETYM_hf0NnFJMPjDy66qmcPLe
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.impute import SimpleImputer
from scipy.stats.mstats import gmean
import random
import warnings
warnings.filterwarnings('ignore')
import gc

def reduce_mem_usage(df, verbose=True):
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    start_mem = df.memory_usage(deep=True).sum() / 1024 ** 2 # just added 
    for col in df.columns:
        col_type = df[col].dtypes
        if col_type in numerics:
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)  
            else:
                if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                    df[col] = df[col].astype(np.float16)
                elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)    
    end_mem = df.memory_usage(deep=True).sum() / 1024 ** 2
    percent = 100 * (start_mem - end_mem) / start_mem
    print('Mem. usage decreased from {:5.2f} Mb to {:5.2f} Mb ({:.1f}% reduction)'.format(start_mem, end_mem, percent))
    return df

"""### **Import Data**"""

train=pd.read_csv('train.csv')
test=pd.read_csv('test.csv')

train.head(3)

train.info()

train.isna().sum()

for df in [train, test]:
  for col in ['CryoSleep','VIP']:
    df[col]=df[col].astype('bool')

for df in [train, test]:
  df.drop('Name', axis=1, inplace=True)

for df in [train, test]:
      reduce_mem_usage(df)

train.info()

#Some passengers are sharing same cabins, so we keep the Cabin column to help the model
train.Cabin.nunique()

def Column_transform(df):
  df['Group']=df['PassengerId'].apply(lambda x: x.split('_')[0])
  #df['Group_no']=df['PassengerId'].apply(lambda x: x.split('_')[1])
  df['deck']=df[df['Cabin'].notnull()]['Cabin'].apply(lambda x: x.split('/')[0])
  df['deck_num']=df[df['Cabin'].notnull()]['Cabin'].apply(lambda x: x.split('/')[1])
  df['deck_side']=df[df['Cabin'].notnull()]['Cabin'].apply(lambda x: x.split('/')[2])
  df.drop('PassengerId', axis=1, inplace=True)
  #df.drop('Cabin', axis=1, inplace=True)
  return df

train_1=Column_transform(train)
test_1=Column_transform(test)

train_1.info()

train_1.head(3)

gc.collect()

"""**Zero Age Adjusted & ##Age Missing Values(not necessary for CatBoost to handle NaN)**"""

def Age_adjust(train, test):
  test['Transported']=3
  df=pd.concat([train,test])
  mean_age=df.loc[(df['Age']!=0)&(~df['Age'].isnull()), 'Age'].astype(float).mean()
  df.loc[(df['Age']==0) | (df['Age'].isnull()), 'Age']=mean_age
    
  tr_fll=df[df['Transported']!=3]
  te_fll=df[df['Transported']==3].drop('Transported', axis=1)
  return tr_fll, te_fll

train_1, test_1=Age_adjust(train_1, test_1)

"""**Handling Missing values**"""

numeric_cols=['RoomService','FoodCourt','ShoppingMall','Spa','VRDeck']
def num_fillna(train_df, test_df):
  test_df['Transported']=3
  df=pd.concat([train_df,test_df])
  for col in numeric_cols:
    M=df[col].astype(float).mean()
    df[col]=df[col].fillna(M)
  tr_fll=df[df['Transported']!=3]
  te_fll=df[df['Transported']==3].drop('Transported', axis=1)
  return tr_fll, te_fll

train_2, test_2 = num_fillna(train_1, test_1)

train_2.isna().sum()

#cat_cols=['HomePlanet','CryoSleep','Destination','VIP','deck','deck_num','deck_side']
#def cat_fillna (train_df, test_df):
  #test_df['Transported']=3
  #df=pd.concat([train_df,test_df])
  #for col in cat_cols:
   # df[col+"_fill"]=np.where(df[col].isnull(), 1, 0)
   # fill=df[col].value_counts().reset_index().iloc[0,0]
  #  df[col]=df[col].fillna(fill)
 # tr_fll=df[df['Transported']!=3]
 # te_fll=df[df['Transported']==3].drop('Transported', axis=1)
 # return tr_fll, te_fll

#train_3, test_3 = cat_fillna(train_2, test_2)

#train_3.isna().sum()

del train_1, test_1
gc.collect()

train_2.info()

train_2['Transported']=train_2['Transported'].astype('bool')

test_2.isna().sum()

"""## **EDA**

### **Correlation**
"""

sns.set_style(style='white')
corr=train_2.corr()
mask=np.triu(np.ones_like(corr, dtype=np.bool))
f, ax =plt.subplots(figsize=(10,8))
cmap = sns.diverging_palette(220, 10, as_cmap=True)
plt.title('Correlation Matrix', fontsize=18)
sns.heatmap(corr, cmap=cmap, mask=mask, vmax=.3, center=0,
            square=True, linewidths=.5, cbar_kws={"shrink": .5}, annot=True)
plt.show()

"""### **Feature Engineering**"""

# we do label encoding to reduce memory usage and make sure we don't have nans

from sklearn.preprocessing import LabelEncoder

lbl_encode_cols=[col for col in train_2.columns if col not in ['Transported']]
for f in lbl_encode_cols:
        if train_2[f].dtype=='object' or test_2[f].dtype=='object':
            train_2[f] = train_2[f].fillna('unseen_before_label')
            test_2[f] = test_2[f].fillna('unseen_before_label')
            lbl = LabelEncoder()
            lbl.fit(list(train_2[f].values) + list(test_2[f].values))
            train_2[f] = lbl.transform(list(train_2[f].values))
            test_2[f] = lbl.transform(list(test_2[f].values))
            train_2[f] = train_2[f].astype('category')
            test_2[f] = test_2[f].astype('category')

"""Total Billed"""

Billed_col=['RoomService','FoodCourt','ShoppingMall','Spa','VRDeck']
def total_billed(df, billed_col): 
  df['Total_billed']=df[billed_col].sum(axis=1)
  return df

train_3=total_billed(train_2, Billed_col)
test_3=total_billed(test_2, Billed_col)

train_3.columns

"""**FE** Billed"""

def FE_billed(train,test):
  test['Transported']=3
  df=pd.concat([train,test])
  df['avg_group']=df.groupby('Group')['Total_billed'].transform('mean')
  df['avg_Cabin']=df.groupby('Cabin')['Total_billed'].transform('mean')
  df['avg_homeplanet']=df.groupby('HomePlanet')['Total_billed'].transform('mean')
  df['avg_Destination']=df.groupby('Destination')['Total_billed'].transform('mean')
  df['avg_VIP']=df.groupby('VIP')['Total_billed'].transform('mean')
  df['avg_deck']=df.groupby('deck')['Total_billed'].transform('mean')
  df['avg_deck_side']=df.groupby('deck_side')['Total_billed'].transform('mean')
  
  df['med_group']=df.groupby('Group')['Total_billed'].transform('median')
  df['med_Cabin']=df.groupby('Cabin')['Total_billed'].transform('median')
  df['med_homeplanet']=df.groupby('HomePlanet')['Total_billed'].transform('median')
  df['med_Destination']=df.groupby('Destination')['Total_billed'].transform('median')
  df['med_VIP']=df.groupby('VIP')['Total_billed'].transform('median')
  df['med_deck']=df.groupby('deck')['Total_billed'].transform('median')
  df['med_deck_side']=df.groupby('deck_side')['Total_billed'].transform('median')
  
  tr_fll=df[df['Transported']!=3]
  te_fll=df[df['Transported']==3].drop('Transported', axis=1)
  return tr_fll, te_fll

train_4, test_4=FE_billed(train_3, test_3)

train_4.info()

del train_2, test_2, train_3, test_3
gc.collect()

"""**Special Services Sum**"""

Special_col=['RoomService','Spa','VRDeck']
def FE_Special_Service(train,test):
  test['Transported']=3
  df=pd.concat([train,test])
  df['Special_service']=df[Special_col].sum(axis=1)

  df['Spec_avg_group']=df.groupby('Group')['Special_service'].transform('mean')
  df['Spec_avg_Cabin']=df.groupby('Cabin')['Special_service'].transform('mean')
  df['Spec_avg_homeplanet']=df.groupby('HomePlanet')['Special_service'].transform('mean')
  df['Spec_avg_Destination']=df.groupby('Destination')['Special_service'].transform('mean')
  df['Spec_avg_VIP']=df.groupby('VIP')['Special_service'].transform('mean')
  df['Spec_avg_deck']=df.groupby('deck')['Special_service'].transform('mean')
  df['Spec_avg_deck_side']=df.groupby('deck_side')['Special_service'].transform('mean')
  
  df['Spec_med_group']=df.groupby('Group')['Special_service'].transform('median')
  df['Spec_med_Cabin']=df.groupby('Cabin')['Special_service'].transform('median')
  df['Spec_med_homeplanet']=df.groupby('HomePlanet')['Special_service'].transform('median')
  df['Spec_med_Destination']=df.groupby('Destination')['Special_service'].transform('median')
  df['Spec_med_VIP']=df.groupby('VIP')['Special_service'].transform('median')
  df['Spec_med_deck']=df.groupby('deck')['Special_service'].transform('median')
  df['Spec_med_deck_side']=df.groupby('deck_side')['Special_service'].transform('median')

  tr_fll=df[df['Transported']!=3]
  te_fll=df[df['Transported']==3].drop('Transported', axis=1)
  return tr_fll, te_fll

train_5, test_5=FE_Special_Service(train_4, test_4)

"""**FE Transported**

one reason for OverFit:
"""

#for df in [train_5,test_5]:
   #df['avg_HomePlanet_Trns']=train_5.groupby('HomePlanet')['Transported'].transform('mean')
   #df['avg_Cabin_Trns']=train_5.groupby('Cabin')['Transported'].transform('mean')
   #df['avg_CryoSleep_Trns']=train_5.groupby('CryoSleep')['Transported'].transform('mean')
   #df['avg_Destination_Trns']=train_5.groupby('Destination')['Transported'].transform('mean')
   #df['avg_Group_Trns']=train_5.groupby('Group')['Transported'].transform('mean')
  # df['avg_Group_no_Trns']=train_5.groupby('Group_no')['Transported'].transform('mean')
  # df['avg_deck_Trns']=train_5.groupby('deck')['Transported'].transform('mean')
  # df['avg_deck_num_Trns']=train_5.groupby('deck_num')['Transported'].transform('mean')
  # df['avg_deck_side_Trns']=train_5.groupby('deck_side')['Transported'].transform('mean')

"""**FE-Age**"""

def Age_transported(train, test):
  test['Transported']=3
  df=pd.concat([train,test])
  mask_1=train['Age']<=20
  mask_2=(train['Age']>20) & (train['Age']<=40)
  mask_3=(train['Age']>40) & (train['Age']<=60)
  mask_4=(train['Age']>60)
  mean_mask_1=train.loc[mask_1, 'Transported'].mean()
  mean_mask_2=train.loc[mask_2, 'Transported'].mean()
  mean_mask_3=train.loc[mask_3, 'Transported'].mean()
  mean_mask_4=train.loc[mask_4, 'Transported'].mean()

  mask_1_df=df['Age']<=20
  mask_2_df=(df['Age']>20) & (df['Age']<=40)
  mask_3_df=(df['Age']>40) & (df['Age']<=60)
  mask_4_df=(df['Age']>60)

  df.loc[mask_1_df, 'Age_transported']=mean_mask_1
  df.loc[mask_2_df, 'Age_transported']=mean_mask_2
  df.loc[mask_3_df, 'Age_transported']=mean_mask_3
  df.loc[mask_4_df, 'Age_transported']=mean_mask_4

  tr_fll=df[df['Transported']!=3]
  te_fll=df[df['Transported']==3].drop('Transported', axis=1)
  return tr_fll, te_fll

#train_6, test_6=Age_transported(train_5, test_5)

#del train_5, test_5, train_4, test_4
gc.collect()

#train_6.info()

trans_to_category=['Cabin', 'Group','deck_num']
for df in [train_5, test_5]:
  for col in trans_to_category:
    df[col]=df[col].astype('category')

#def freq_encode_full(df1, df2, col, normalize=True):
   # df = pd.concat([df1[col],df2[col]])
   # vc = df.value_counts(dropna=False, normalize=normalize).to_dict()
  #  nm = col + '_FE_FULL'
   # df1[nm] = df1[col].map(vc)
  #  df1[nm] = df1[nm].astype('float32')
  #  df2[nm] = df2[col].map(vc)
   # df2[nm] = df2[nm].astype('float32')
  #  return nm

# freq_encode_full(train_6, test_6,...)

train_5.isna().sum()

cat_cols=[col for col in list(train_5) if train_5[col].dtype in ['category'] ]
cat_cols

for df in [train_5, test_5]:
      reduce_mem_usage(df)

"""**Defining CATBoost model**"""

! pip install catboost

from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score

def seed_everything(seed=0):
    random.seed(seed)
    np.random.seed(seed)

SEED = 42
seed_everything(SEED)
NFOLDS = 5

train_5['Transported']=train_5['Transported'].astype('int')

X=train_5.drop('Transported', axis=1)
y=train_5['Transported']
X_test=test_5

def train_val_split_by_time(X, y, test_size=0.2):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=test_size, shuffle=False)
    
    print(f'train.shape: {X_train.shape}, val.shape: {X_val.shape}')
    
    return X_train, y_train, X_val, y_val

X_train, y_train, X_val, y_val=train_val_split_by_time(X, y, test_size=0.2)

cat_params = {
    'n_estimators':5000,
    'learning_rate': 0.07,
    'eval_metric':'AUC',
    'loss_function':'Logloss',
    'random_seed':SEED,
    'metric_period':500,#The frequency of iterations to calculate the values of objectives and metrics.
    'od_wait':500,#The number of iterations to continue the training after the iteration with the optimal metric value.
    'task_type':'GPU',
    'depth': 8,
    #'colsample_bylevel':0.7,
}

def make_val_prediction(X_train, y_train, X_val, y_val, seed=SEED, seed_range=3, cat_params=cat_params,
                        category_cols=None):
    print(X_train.shape, X_val.shape)
    
    acc_arr = []
    best_iteration_arr = []
    preds = np.zeros((X_val.shape[0], seed_range))
    preds_score=np.zeros((X_val.shape[0], seed_range))

    for i, s in enumerate(range(seed, seed + seed_range)):
        seed_everything(s)
        params = cat_params.copy()
        params['random_seed'] = s
        
        clf = CatBoostClassifier(**params)
        clf.fit(X_train, y_train, eval_set=(X_val, y_val),
                cat_features=category_cols,
                use_best_model=True,
                verbose=True)

        best_iteration = clf.best_iteration_
        best_iteration_arr.append(best_iteration)
        
        pred = clf.predict_proba(X_val)[:,1]
        pred_score=clf.predict(X_val)
        #preds_score[:,i]=pred_score "we don't need it cause mean of preds which are 0 or 1 is meaningless"
        #preds[:, i] = pred
        accuracy = accuracy_score(y_val, pred_score)
        acc_arr.append(accuracy)
        print('seed:', s, ', accuracy:', accuracy, ', best_iteration:', best_iteration)

    acc_arr = np.array(acc_arr)
    best_iteration_arr = np.array(best_iteration_arr)
    best_iteration = int(np.mean(best_iteration_arr))
    #avg_preds_acc = accuracy_score(y_val, np.mean(preds_score, axis=1)) "mean of preds_score which are 0 or 1 is not useful"

    print(f'avg accuracy: {np.mean(acc_arr):.5f}+/-{np.std(acc_arr):.5f}, avg best iteration: {best_iteration}')
    
    return best_iteration

def make_test_prediction(X, y, X_test, best_iteration, seed=SEED, category_cols=None):
    print('best iteration:', best_iteration)
    preds = np.zeros((X_test.shape[0], NFOLDS))
    val_preds=np.zeros(X.shape[0])

    print(X.shape, X_test.shape)
    
    skf = StratifiedKFold(n_splits=NFOLDS, shuffle=True, random_state=seed)
    params = cat_params.copy()
    params['n_estimators'] = best_iteration
    
    for i, (trn_idx, te_idx) in enumerate(skf.split(X, y)):
        fold = i + 1
        print('Fold:',fold)
        
        tr_x, tr_y = X.iloc[trn_idx,:], y.iloc[trn_idx]
            
        print(len(tr_x))
        clf = CatBoostClassifier(**params)
        clf.fit(tr_x, tr_y, cat_features=category_cols, 
                use_best_model=False, verbose=True)
        
        val_preds[te_idx]+= clf.predict_proba(X.iloc[te_idx])[:,1]
        preds[:, i] = clf.predict_proba(X_test)[:,1]
    
    return preds, val_preds

"""**Train the model**"""

best_iteration1= make_val_prediction(X_train, y_train, X_val,
                                                 y_val, category_cols=cat_cols)

preds, val_preds = make_test_prediction(X, y, X_test, best_iteration1, category_cols=cat_cols)

"""**Creating Submission**"""

np.save('preds_cat.npy',preds)
np.save('val_preds_cat.npy', val_preds)

preds=gmean(preds, axis=1)

from sklearn.metrics import f1_score

def to_labels(pos_probs, threshold):
	return (pos_probs >= threshold).astype('int')
 
thresholds = np.arange(0, 1, 0.001)
scores = [f1_score(y, to_labels(val_preds, t)) for t in thresholds]
ix = np.argmax(scores)
print('Threshold=%.3f, F-Score=%.5f' % (thresholds[ix], scores[ix]))

preds=np.where(preds<thresholds[ix], 0, 1)

preds=preds.astype('bool')

submission=pd.read_csv('sample_submission.csv')

submission.head()

submission.drop('Transported', axis=1, inplace=True)

submission['Transported']=preds

submission.head()

submission.to_csv('submission.csv', index=False)