from flask import Flask, request, jsonify, Response
import requests
import pydicom
import torch
import io
import pickle
from torchvision import transforms
import torchvision.transforms.functional as TF
from torchvision.transforms import functional as F
app = Flask(__name__)

@app.route('/dicom_to_labelled_tensor', methods=['POST'])
def dicom_to_labelled_tensor():
    """
    Convert DICOM image to labelled tensor.

    Returns:
        Response: Serialized labelled tensor as a pickle file.
    """
    # Access data from form data
    uri = request.form.get('uri')
    contrast = request.form.get('contrast')

    if not uri or not contrast:
        return jsonify({'error': 'Missing URI or contrast'}), 400

    if 'zenodo' in uri or 'b2share' in uri:
        download_url = uri
    else:
        return jsonify({'error': 'Image conversion failed.'}), 400
    
    try:
        head_response = requests.head(download_url)
        content_type = head_response.headers.get('Content-Type', '')
        if 'dicom' not in content_type and 'octet-stream' not in content_type:
            return jsonify({'error': 'URI does not point to a DICOM file based on Content-Type'}), 400
    except requests.RequestException as e:
        return jsonify({'error': f'Error making HEAD request: {e}'}), 400

    response = requests.get(download_url)
    response.raise_for_status()

    dicom_data = pydicom.dcmread(io.BytesIO(response.content), force=True)
    pixel_array = dicom_data.pixel_array
    if contrast == 'T1-weighted':
        label = 1
    elif contrast == 'T2-weighted':
        label = 2
    elif contrast == 'PD-weighted':
        label = 3
    else:
        return jsonify({'error': 'Image conversion failed.'}), 400

    pixel_tensor = torch.tensor(pixel_array)
    pixel_tensor = pixel_tensor.unsqueeze(0)
    label_tensor = torch.tensor(label)

    result = (pixel_tensor, label_tensor)
    serialized_data = pickle.dumps(result)

    response = Response(serialized_data, status=200, mimetype='application/octet-stream')
    response.headers['Content-Disposition'] = 'attachment; filename="tensor_data.pkl"'
    response.headers['Message'] = 'Image successfully converted.'
    return response

def augment_images(label_tensor, image_tensor):
    """
    Augment images by rotating them and replicating the label tensor.

    Args:
        label_tensor (torch.Tensor): Label tensor.
        image_tensor (torch.Tensor): Image tensor.

    Returns:
        tuple: Stacked augmented image tensors and stacked label tensors.
    """
    augmented_image_tensors = []
    augmented_label_tensors = []
    # Define rotation parameters
    angles = torch.linspace(0, 360, 100)

    # Handling batches of images
    for i in range(image_tensor.size(0)):  # Iterate through each image in the batch
        single_image_tensor = image_tensor[i]

        # Ensure the tensor has a channel dimension
        if single_image_tensor.dim() == 2:  # Grayscale image without channel dimension
            single_image_tensor = single_image_tensor.unsqueeze(0)  # Add channel dimension
            
        for angle in angles:
        # Rotate the image
            rotated_image = F.rotate(image_tensor, angle.item())
            # Add the rotated image tensor to the list
            augmented_image_tensors.append(rotated_image)
            
            # Assuming label_tensor should be replicated for each image
            augmented_label_tensors.append(label_tensor.clone())

    # Stack all augmented tensors into a single tensor
    stacked_image_tensors = torch.stack(augmented_image_tensors, dim=0)
    stacked_label_tensors = torch.stack(augmented_label_tensors, dim=0)
    return (stacked_image_tensors, stacked_label_tensors)


@app.route('/labeled_tensor_augment', methods=['POST'])
def labeled_tensor_augment():
    """
    Augment labeled tensor by rotating the image tensor.

    Returns:
        Response: Serialized augmented labeled tensor as a pickle file.
    """
    if 'tensor' not in request.files:
        return jsonify({'error': 'Image augmentation failed.'}), 400

    file = request.files['tensor']
    if file.filename == '':
        return jsonify({'error': 'Image augmentation failed.'}), 400

    # Read the pickle file and extract the tuple
    try:
        image_tensor, label_tensor = pickle.load(file.stream)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    result_tuple = augment_images(label_tensor, image_tensor)

    serialized_data = pickle.dumps(result_tuple)

    response = Response(serialized_data, status=200, mimetype='application/octet-stream')
    response.headers['Message'] = 'Image successfully augmented.'
    response.headers['Content-Disposition'] = 'attachment; filename="tensor_data.pkl"'
    return response


def normalize_standardize_image(image_tensor):
    """
    Normalize and standardize the image tensor.

    Args:
        image_tensor (torch.Tensor): Image tensor.

    Returns:
        torch.Tensor: Normalized and standardized image tensor.
    """
    # Convert image tensor to floating point
    
    image_tensor = image_tensor.to(torch.float32)
    print(image_tensor)
    # Check the number of dimensions of the tensor
    if image_tensor.dim() == 3:  # For single grayscale image (H, W)
        image_tensor = image_tensor.unsqueeze(0)  # Convert to (1, H, W)
    elif image_tensor.dim() == 2:  # For single grayscale image without channel dimension
        image_tensor = image_tensor.unsqueeze(0).unsqueeze(0)  # Convert to (1, 1, H, W)

    # Check if the image tensor is normalized
    image_tensor = image_tensor / 255
    # Define the normalization transform
    normalize = transforms.Normalize(mean=[0.5], std=[0.5])
    normalized_image_tensor = normalize(image_tensor)

    return normalized_image_tensor

@app.route('/labeled_tensor_normalize', methods=['POST'])
def labeled_tensor_normalize():
    """
    Normalize and standardize the labeled tensor.

    Returns:
        Response: Serialized normalized labeled tensor as a pickle file.
    """
    if 'tensor' not in request.files:
        return jsonify({'error': 'Image normalization and standardization failed.'}), 400

    file = request.files['tensor']
    if file.filename == '':
        return jsonify({'error': 'Image normalization and standardization failed.'}), 400

    # Read the pickle file and extract the tuple
    try:
        image_tensor, label_tensor = pickle.load(file.stream)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Normalize and standardize the image tensor
    normalized_image_tensor = normalize_standardize_image(image_tensor)

    # Create a new tuple with the label and normalized image tensors
    normalized_tuple = (normalized_image_tensor, label_tensor)

    # Convert the normalized tuple to a JSON string
    serialized_data = pickle.dumps(normalized_tuple)

    response = Response(serialized_data, status=200, mimetype='application/octet-stream')
    response.headers['Message'] = 'Image successfully normalized and standardized.'
    response.headers['Content-Disposition'] = 'attachment; filename="tensor_data.pkl"'
    return response


@app.route('/labeled_tensor_resize', methods=['POST'])
def labelled_tensor_resize():
    """
    Resize the image tensor in the labeled tensor.

    Returns:
        Response: Serialized resized labeled tensor as a pickle file.
    """
    if 'tensor' not in request.files:
        return jsonify({'error': 'Image resizing failed.'}), 400

    file = request.files['tensor']
    if file.filename == '':
        return jsonify({'error': 'Image resizing failed.'}), 400

    # Read the pickle file and extract the tuple
    try:
        image_tensor, label_tensor = pickle.load(file.stream)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Check if the tensor is a single image or a batch of images
    if image_tensor.dim() == 3:  # Single image
        image_tensor = image_tensor.unsqueeze(0)  # Add batch dimension

    # Resize the image tensor to 256x256 using OpenCV
    resize_transform = transforms.Resize((256, 256))
    resized_image = resize_transform(image_tensor)

     # Remove the batch dimension if it was a single image
    if resized_image.shape[0] == 1:
        resized_image = resized_image.squeeze(0)

    # Create the output tuple with the label tensor and resized image tensor
    output_tuple = (resized_image, label_tensor)
    
    # Convert the normalized tuple to a JSON string
    serialized_data = pickle.dumps(output_tuple)

    response = Response(serialized_data, status=200, mimetype='application/octet-stream')
    response.headers['Message'] = 'Image successfully resized.'
    response.headers['Content-Disposition'] = 'attachment; filename="tensor_data.pkl"'
    return response

if __name__ == '__main__':
    app.run(port=5002)