import numpy as np

from backend.tools.model_inference import (
    vectorize_features,
    FEATURE_LIST,
    create_dummy_model,
    predict_proba_from_features,
)


def test_vectorize_features_order_and_length():
    features = {name: i for i, name in enumerate(FEATURE_LIST)}
    x = vectorize_features(features)
    assert x.shape == (len(FEATURE_LIST),)
    # Position 0 should equal 0, position 1 -> 1, etc.
    assert x[0] == 0.0 and x[1] == 1.0


def test_dummy_model_predicts_probability():
    model = create_dummy_model()
    feats = {name: 0.0 for name in FEATURE_LIST}
    x = vectorize_features(feats).reshape(1, -1)
    p = float(model.predict_proba(x)[0, 1])
    assert 0.0 <= p <= 1.0


def test_predict_from_features_returns_confidence():
    feats = {name: 0.0 for name in FEATURE_LIST}
    out = predict_proba_from_features(feats)
    assert 'prob_up' in out and 'confidence' in out and 'predicted_class' in out
    assert 0.0 <= out['prob_up'] <= 1.0
    assert 0.0 <= out['confidence'] <= 1.0


