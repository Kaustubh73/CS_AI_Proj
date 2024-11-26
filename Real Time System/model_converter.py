# model_converter.py
import numpy as np
import onnx
import onnxruntime
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pandas as pd

def convert_random_forest_to_onnx(model, features, output_path='random_forest_model2.onnx'):
    """
    Convert a Random Forest Classifier to ONNX format
    
    Args:
    - model: Trained RandomForestClassifier
    - features: List of feature names
    - output_path: Path to save the ONNX model
    
    Returns:
    - onnx_model: Converted ONNX model
    """
    # Prepare initial types for input features
    initial_type = [('float_input', FloatTensorType([None, len(features)]))]
    
    # Convert the model
    onnx_model = convert_sklearn(
        model, 
        initial_types=initial_type,
        target_opset=12  # Specify ONNX opset version
    )
    
    # Save the model
    onnx.save_model(onnx_model, output_path)
    
    print(f"Model converted and saved to {output_path}")
    return onnx_model

def verify_onnx_model(onnx_model, X_test):
    """
    Verify ONNX model prediction matches sklearn model
    
    Args:
    - onnx_model: Converted ONNX model
    - X_test: Test features
    
    Returns:
    - predictions: ONNX model predicted classes
    - probabilities: ONNX model predicted probabilities for each class
    """
    # Create ONNX Runtime inference session
    sess = onnxruntime.InferenceSession(onnx_model.SerializeToString())
    
    # Prepare input
    input_name = sess.get_inputs()[0].name
    
    # Convert input to float32
    X_test_float = X_test.astype(np.float32)
    
    # Run inference
    input_dict = {input_name: X_test_float}
    outputs = sess.run(None, input_dict)
    
    # The first output is predicted classes, the second is probabilities
    predictions = outputs[0]  # Predicted class labels
    probabilities = outputs[1]  # Predicted probabilities
    print(probabilities[0])
    return predictions, probabilities

# Example usage script
def main():
    # Load your dataset (replace with your actual data loading)
    # This is an example, use your actual data loading method
    oversampled_data = pd.read_csv('/home/eeiith/Desktop/Project1/Kaustubh/CS_AI_Proj/Data Augmentation/combinedData_SMOTE_Oversampling.csv')
    print("Data loaded")
    oversampled_data['Content_present'] = oversampled_data['ContentLen'].notnull().astype(int)
    features = ['Method', 'ReqLen', 'ArgLen', 'NumArgs', 'NumDigitsArgs', 
                'PathLen', 'NumLettersArgs', 'NumLettersPath', 'NumSpecialCharsPath', 
                'MaxByteValReq', 'Content_present']
    X_train = oversampled_data.drop(columns=['class'])
    X_train = X_train[features]
    y_train = oversampled_data['class']    
    
    X_test = X_train.sample(frac=0.2, random_state=42)
    print("Data split")
    # Train Random Forest model
    print("Training model")
    # rf_model = RandomForestClassifier(random_state=42)
    # rf_model.fit(X_train, y_train)
    print("Model trained")
    # Convert to ONNX
    print("Converting model")
    # onnx_model = convert_random_forest_to_onnx(
    #     rf_model, 
    #     features,     # have 0.2 of the data as test set

    #     output_path='random_forest_hijacking_model.onnx'
    # )
    # Load ONNX model
    onnx_model = onnx.load("random_forest_hijacking_model.onnx")
    print("Model converted")
    # Verify model conversion
    print("Verifying model")
    onnx_predictions, onnx_probabilities = verify_onnx_model(onnx_model, X_test.values)
    
    print("Model verified")

    # Compare predictions
    # sklearn_predictions = rf_model.predict(X_test)
    # sklearn_probabilities = rf_model.predict_proba(X_test)

    # print("Prediction match:", np.array_equal(sklearn_predictions, onnx_predictions))
    # print("Probability match:", np.allclose(sklearn_probabilities, onnx_probabilities, atol=1e-6))
    print("Onnx Predictions",onnx_predictions)
    print("Onnx Probabilities",onnx_probabilities)
    # print("Sklearn Probabilities",sklearn_probabilities)
if __name__ == "__main__":
    main()

# requirements.txt additional dependencies
"""
scikit-learn==1.2.2
skl2onnx==1.14.1
onnx==1.14.0
"""