import os, json
from pathlib import Path
import requests
import streamlit as st
st.title('ExtraaLearn Lead Conversion')
st.caption('Decision support, not a guarantee of conversion. Scores are not calibrated probabilities.')
BASE=Path(__file__).resolve().parent
schema=json.loads((BASE/'schema.json').read_text())
with st.form('lead'):
    payload={}
    for col in schema['columns']:
        if col in schema['categories']:
            payload[col]=st.selectbox(col,schema['categories'][col])
        elif col=='page_views_per_visit':
            payload[col]=st.number_input(col,min_value=0.0,value=3.0)
        else:
            payload[col]=st.number_input(col,min_value=0,value=40 if col=='age' else 3,step=1)
    submit=st.form_submit_button('Predict')
if submit:
    endpoint=os.getenv('API_URL','http://localhost:7860').rstrip('/')+'/predict'
    try:
        response=requests.post(endpoint,json=payload,timeout=30)
        response.raise_for_status()
        result=response.json()
        st.metric('Conversion score',f"{result['conversion_score']:.1%}")
        st.write('Likely converter' if result['prediction']==1 else 'Lower-priority lead')
        st.json(result)
    except (requests.RequestException,ValueError) as exc:
        st.error('Prediction request failed. Check API_URL and backend availability.')
        st.code(str(exc))
