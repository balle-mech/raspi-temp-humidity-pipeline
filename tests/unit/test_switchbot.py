import json
from unittest.mock import MagicMock, patch

from automation.switchbot import make_sign, send_command


class TestMakeSign:
    def test_known_vector(self):
        sign = make_sign("token123", "secret123", "1700000000000", "nonce-abc")
        assert sign == "/ZHBmUjlD0pSSBKBH0poS7va0v4POlrVP3/asR5ExpM="


class TestSendCommand:
    @patch("automation.switchbot.urlopen")
    def test_posts_turn_off_command(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"statusCode": 100}).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = send_command("device-1", "turnOff", token="tok", secret="sec")

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://api.switch-bot.com/v1.1/devices/device-1/commands"
        assert req.get_method() == "POST"
        body = json.loads(req.data.decode())
        assert body == {"command": "turnOff", "parameter": "default", "commandType": "command"}
        assert req.get_header("Authorization") == "tok"
        for header in ("Sign", "T", "Nonce"):
            assert req.get_header(header)
        assert result["statusCode"] == 100
