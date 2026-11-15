import json, math, os
from pathlib import Path
import joblib
import pandas as pd
from flask import Flask, request, jsonify
BASE=Path(__file__).resolve().parent
model=joblib.load(BASE/'model.joblib')
schema=json.loads((BASE/'schema.json').read_text())
app=Flask(__name__)
@app.get('/health')
def health():
    return jsonify(status='ok')
@app.post('/predict')
def predict():
    body=request.get_json(silent=True)
    if not isinstance(body,dict):
        return jsonify(error='Expected one JSON object containing all predictor fields'),400
    missing=sorted(set(schema['columns'])-set(body))
    extra=sorted(set(body)-set(schema['columns']))
    if missing or extra:
        return jsonify(error='Schema mismatch',missing=missing,extra=extra),400
    errors=[]
    for col in schema['numeric']:
        v=body[col]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0:
            errors.append(col+': expected finite nonnegative number')
        elif col in ['age','website_visits','time_spent_on_website'] and v!=int(v):
            errors.append(col+': expected integer')
    for col,allowed in schema['categories'].items():
        if not isinstance(body[col],str) or body[col] not in allowed:
            errors.append(col+': expected one of '+str(allowed))
    if errors:
        return jsonify(error='Invalid values',details=errors),400
    frame=pd.DataFrame([body],columns=schema['columns'])
    probability=float(model.predict_proba(frame)[0,1])
    prediction=int(model.predict(frame)[0])
    return jsonify(prediction=prediction,conversion_score=probability,threshold=0.5,
                   note='Model score is not a calibrated conversion probability')
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','7860')),debug=False)
