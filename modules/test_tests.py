import unittest
from flask import Flask
import io
import pickle
import torch
from torchvision import transforms  

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_dicom_to_labelled_tensor(self):
        # Create a mock DICOM image
        dicom_image = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
        # Create a mock form data
        form_data = {
            'uri': 'https://example.com/dicom_image.dcm',
            'contrast': 'T1-weighted'
        }
        # Send a POST request to the endpoint
        response = self.client.post('/dicom_to_labelled_tensor', data=form_data, content_type='multipart/form-data', data={'file': (io.BytesIO(dicom_image), 'dicom_image.dcm')})
        # Check the response status code
        self.assertEqual(response.status_code, 200)
        # Check the response content type
        self.assertEqual(response.content_type, 'application/octet-stream')
        # Check the response headers
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="tensor_data.pkl"')
        self.assertEqual(response.headers['Message'], 'Image successfully converted.')
        # Deserialize the response data
        result = pickle.loads(response.data)
        # Check the result
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], torch.Tensor)
        self.assertIsInstance(result[1], torch.Tensor)

    def test_labeled_tensor_augment(self):
        # Create a mock labeled tensor
        labeled_tensor = (torch.tensor([1, 2, 3]), torch.tensor([4]))
        # Serialize the labeled tensor
        serialized_data = pickle.dumps(labeled_tensor)
        # Send a POST request to the endpoint
        response = self.client.post('/labeled_tensor_augment', data={'tensor': (io.BytesIO(serialized_data), 'labeled_tensor.pkl')})
        # Check the response status code
        self.assertEqual(response.status_code, 200)
        # Check the response content type
        self.assertEqual(response.content_type, 'application/octet-stream')
        # Check the response headers
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="tensor_data.pkl"')
        self.assertEqual(response.headers['Message'], 'Image successfully augmented.')
        # Deserialize the response data
        result = pickle.loads(response.data)
        # Check the result
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], torch.Tensor)
        self.assertIsInstance(result[1], torch.Tensor)

    def test_labeled_tensor_normalize(self):
        # Create a mock labeled tensor
        labeled_tensor = (torch.tensor([1, 2, 3]), torch.tensor([4]))
        # Serialize the labeled tensor
        serialized_data = pickle.dumps(labeled_tensor)
        # Send a POST request to the endpoint
        response = self.client.post('/labeled_tensor_normalize', data={'tensor': (io.BytesIO(serialized_data), 'labeled_tensor.pkl')})
        # Check the response status code
        self.assertEqual(response.status_code, 200)
        # Check the response content type
        self.assertEqual(response.content_type, 'application/octet-stream')
        # Check the response headers
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="tensor_data.pkl"')
        self.assertEqual(response.headers['Message'], 'Image successfully normalized and standardized.')
        # Deserialize the response data
        result = pickle.loads(response.data)
        # Check the result
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], torch.Tensor)
        self.assertIsInstance(result[1], torch.Tensor)

    def test_labeled_tensor_resize(self):
        # Create a mock labeled tensor
        labeled_tensor = (torch.tensor([1, 2, 3]), torch.tensor([4]))
        # Serialize the labeled tensor
        serialized_data = pickle.dumps(labeled_tensor)
        # Send a POST request to the endpoint
        response = self.client.post('/labeled_tensor_resize', data={'tensor': (io.BytesIO(serialized_data), 'labeled_tensor.pkl')})
        # Check the response status code
        self.assertEqual(response.status_code, 200)
        # Check the response content type
        self.assertEqual(response.content_type, 'application/octet-stream')
        # Check the response headers
        self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename="tensor_data.pkl"')
        self.assertEqual(response.headers['Message'], 'Image successfully resized.')
        # Deserialize the response data
        result = pickle.loads(response.data)
        # Check the result
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], torch.Tensor)
        self.assertIsInstance(result[1], torch.Tensor)

if __name__ == '__main__':
    unittest.main()

