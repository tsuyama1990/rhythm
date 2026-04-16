import os
import requests
from typing import Dict, List, Optional


class JQuantsClient:
    BASE_URL = "https://api.jquants.com/v1"

    def __init__(
        self, mail_address: Optional[str] = None, password: Optional[str] = None
    ):
        self.mail_address = mail_address or os.getenv("JQUANTS_MAIL_ADDRESS")
        self.password = password or os.getenv("JQUANTS_PASSWORD")

        if not self.mail_address or not self.password:
            raise ValueError(
                "JQUANTS_MAIL_ADDRESS and JQUANTS_PASSWORD must be provided or set in environment variables."
            )

        self.refresh_token: Optional[str] = None
        self.id_token: Optional[str] = None

    def _get_refresh_token(self) -> str:
        self.refresh_token = ""
        url = f"{self.BASE_URL}/token/auth_user"
        data = {"mailaddress": self.mail_address, "password": self.password}
        response = requests.post(url, json=data)
        response.raise_for_status()
        self.refresh_token = response.json().get("refreshToken", "")
        return str(self.refresh_token)

    def _get_id_token(self) -> str:
        self.id_token = ""
        if not self.refresh_token:
            self._get_refresh_token()

        url = f"{self.BASE_URL}/token/auth_refresh"
        params = {"refreshtoken": self.refresh_token}
        response = requests.post(url, params=params)

        if response.status_code != 200:
            # If refresh token is expired or invalid, try getting a new one
            self._get_refresh_token()
            params = {"refreshtoken": self.refresh_token}
            response = requests.post(url, params=params)
            response.raise_for_status()

        self.id_token = response.json().get("idToken", "")
        return str(self.id_token)

    def get_auth_headers(self) -> Dict[str, str]:
        if not self.id_token:
            self._get_id_token()
        return {"Authorization": f"Bearer {self.id_token}"}

    def fetch_listed_info(self, code: Optional[str] = None) -> List[Dict]:
        """Fetch listed company information (stock master)."""
        url = f"{self.BASE_URL}/listed/info"
        params = {}
        if code:
            params["code"] = code

        headers = self.get_auth_headers()
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 403 or response.status_code == 401:
            self._get_id_token()
            headers = self.get_auth_headers()
            response = requests.get(url, headers=headers, params=params)

        response.raise_for_status()
        return response.json().get("info", [])

    def fetch_daily_quotes(
        self,
        code: Optional[str] = None,
        date: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict]:
        """Fetch daily quotes with pagination."""
        url = f"{self.BASE_URL}/prices/daily_quotes"
        params = {}
        if code:
            params["code"] = code
        if date:
            params["date"] = date
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        all_quotes = []
        headers = self.get_auth_headers()

        while True:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code in [401, 403]:
                # Token might be expired
                self._get_id_token()
                headers = self.get_auth_headers()
                response = requests.get(url, headers=headers, params=params)

            response.raise_for_status()
            data = response.json()
            quotes = data.get("daily_quotes", [])
            all_quotes.extend(quotes)

            pagination_key = data.get("pagination_key")
            if not pagination_key:
                break

            params["pagination_key"] = pagination_key

        return all_quotes
