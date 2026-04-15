from unittest.mock import patch, MagicMock
from src.jquants_client import JQuantsClient
import os

@patch.dict(os.environ, {"JQUANTS_MAIL_ADDRESS": "test@example.com", "JQUANTS_PASSWORD": "password123"})
def test_jquants_client_init():
    client = JQuantsClient()
    assert client.mail_address == "test@example.com"
    assert client.password == "password123"
    print("Init test passed.")

@patch('requests.post')
@patch.dict(os.environ, {"JQUANTS_MAIL_ADDRESS": "test@example.com", "JQUANTS_PASSWORD": "password123"})
def test_get_refresh_token(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"refreshToken": "fake_refresh_token"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    client = JQuantsClient()
    token = client._get_refresh_token()

    assert token == "fake_refresh_token"
    assert client.refresh_token == "fake_refresh_token"
    print("Refresh token test passed.")

test_jquants_client_init()
test_get_refresh_token()
