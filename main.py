import streamlit as st
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
import pickle
import datetime
import os
from io import StringIO
from PIL import Image


#Todo
# create new feature (selectable ex time date if timeseries)
# add plot feature (eda) or add plot scatter any graph
# add add feature and try prediction (https://pycaret.gitbook.io/docs/learn-pycaret/official-blog/build-and-deploy-ml-app-with-pycaret-and-streamlit)
# add feature small batches (if dataset is too large we just sample it for efficiency)
# save model (button or automatically)
# (DONE) create function at compare_model() so we can cache increase speed
# add selection number of fold
# explore setup pycaret(data preparation)
# add sort at compare_model (sort by rmse mae r2 etc)
# add config file (store dict)


classification_dict = {'Area Under the Curve':['auc','AUC'],
                       'Discrimination Threshold':['threshold','Threshold'],
                       'Precision Recall Curve':['pr', 'Precision Recall'],
                       'Confusion Matrix':['confusion_matrix', 'Confusion Matrix'],
                       'Class Prediction Error':['error','Prediction Error'],
                       'Classification Report':['class_report', 'Class Report'],
                       'Decision Boundary':['boundary', 'Decision Boundary'],
                       'Recursive Feature Selection':['rfe', 'Feature Selection'],
                       'Learning Curve':['learning', 'Learning Curve'],
                       'Manifold Learning':['manifold', 'Manifold Learning'],
                       'Calibration Curve':['calibration', 'Calibration Curve'],
                       'Validation Curve':['vc', 'Validation Curve'],
                       'Dimension Learning':['dimension', 'Dimensions'],
                       'Feature Importance (Top 10)':['feature','Feature Importance'],
                       'Feature Importance (all)':['feature_all', 'Feature Importance (All)'],
                       'Lift Curve':['lift','lift'],
                       'Gain Curve':['gain', 'gain'],
                       'KS Statistic Plot':['ks','ks']}

regression_dict = {'Residuals Plot':['residuals','Residuals'],
                    'Prediction Error Plot':['error', 'Prediction Error'],
                    'Cooks Distance Plot':['cooks', 'Cooks Distance'],
                    'Recursive Feature Selection':['rfe', 'Feature Selection'],
                    'Learning Curve':['learning', 'Learning Curve'],
                    'Validation Curve':['vc', 'Validation Curve'],
                    'Manifold Learning':['manifold', 'Manifold Learning'],
                    'Feature Importance (top 10)':['feature', 'Feature Importance'],
                    'Feature Importance (all)':['feature_all', 'Feature Importance (All)']}


def init_pycaret():
    st.header('Select column to predict')
    target = tuple(dataframe.columns)
    selected_target = st.selectbox('Select target for prediction', target)
    st.write('selected target :', selected_target)

    st.header('Select train : test ratio')
    traintest = st.slider('train:test:', min_value=0, max_value=100, step=5, value=80)
    train_ratio = traintest / 100
    st.write('train ratio :', train_ratio)
    test_ratio = (100 - traintest) / 100
    st.write('test ratio :', test_ratio)

    return train_ratio, selected_target


@st.cache
def plot_scatter(feature_a,feature_b):
    fig = px.scatter(dataframe, x=feature_a, y=feature_b, trendline="ols")
    fig.update_xaxes(
        rangeslider_visible=True,
    )
    fig.update_layout(
        title='Scatter plot',
        autosize=True, )
    return fig


def initiate_dataframe():
    image = Image.open(f'assets/title.jpg')
    st.image(image)
    st.header('Upload csv file')
    uploaded_file = st.file_uploader("Upload csv file")
    if uploaded_file is None:
        st.stop()
    if uploaded_file is not None:
        try:
            dataframe = pd.read_csv(uploaded_file)
            st.write(dataframe)
        except:
            print('Upload csv file only!!')
    return dataframe, uploaded_file


@st.cache(suppress_st_warning=True,hash_funcs={'xgboost.sklearn.XGBRegressor': id},allow_output_mutation=True)
def setup_pycaret(train_ratio,selected_target):
    s = setup(dataframe, target=selected_target, silent=True, train_size=train_ratio)
    best = compare_models(n_select=3)
    compare_df = pd.DataFrame(pull())
    return best,compare_df

def eda_pycaret():
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.header('EDA')
    st.pyplot(eda(display_format='svg'))

def select_ml():
    st.header('Select machine learning types')
    ml = ('Regression', 'Classification', 'Time series')
    selected_ml = st.selectbox('Select machine learning types', ml)
    st.write('selected machine learning types :', selected_ml)
    return selected_ml


def evaluation_pycaret(selected_ml,selected_model,best):
    if selected_ml == 'Regression':
        dict = regression_dict
    elif selected_ml == 'Classification':
        dict = classification_dict
    st.header('Select evaluation')
    options = st.multiselect(
        'Select evaluation', options=dict.keys()
    )

    for i in options:
        plot_model(best[int(selected_model) - 1], plot=dict[i][0], save=True)
        image = Image.open(f'{dict[i][1]}.png')
        st.header(i)
        st.image(image, caption=i)

def top_3_model(best,selected_target):
    st.header('top 3 model')
    models = ('1', '2', '3')
    selected_model = st.selectbox('Select model (top 3)', models)
    st.write('selected model :', best[int(selected_model) - 1])
    st.header('Predicted dataframe')
    predictions = predict_model(best[int(selected_model) - 1], data=dataframe)
    st.write(predictions.head())

    st.header('Predicted result')
    dictt = {'actual': predictions[selected_target], 'predict': predictions['Label']}
    df_test = pd.DataFrame(dictt)
    st.write(df_test.head())

    return selected_model

def select_scatter():
    st.header('Scatter plot between each feature')
    options = st.multiselect(
        'Select 2 feature',
        options=dataframe.columns)
    try:
        st.plotly_chart(plot_scatter(options[0], options[1]))
    except IndexError:
        st.write('Please select 2 numerical features')
    except ValueError:
        st.write('Please select 2 numerical features')


def pipeline_st():
    train_ratio, selected_target = init_pycaret()
    best, compare_df = setup_pycaret(train_ratio, selected_target)
    eda_pycaret()
    select_scatter()
    st.header('Compare model')
    st.write(compare_df)
    selected_model = top_3_model(best,selected_target)
    evaluation_pycaret(selected_ml, selected_model,best)


# Start
dataframe,uploaded_file = initiate_dataframe()
selected_ml = select_ml()
if selected_ml == 'Regression' and uploaded_file is not None:
    from pycaret.regression import *
    pipeline_st()
elif selected_ml == 'Classification' and uploaded_file is not None:
    from pycaret.classification import *
    pipeline_st()


