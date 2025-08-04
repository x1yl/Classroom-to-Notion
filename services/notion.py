# notion_manager.py
import requests
import os
from typing import List, Dict, Any


class NotionDatabaseManager:
    def __init__(self, database_id: str, token: str = None):
        self.database_id = database_id
        self.token = token or os.environ.get("NOTION_TOKEN")
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def query_database(self, filter_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{self.database_id}/query"
        data = {"filter": {"or": filter_conditions}}
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()

    def get_tasks_by_status(self, statuses: List[str]) -> Dict[str, Any]:
        filter_conditions = [
            {"property": "Status", "status": {"equals": status}} for status in statuses
        ]
        return self.query_database(filter_conditions)

    def get_database_properties(self) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{self.database_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_database_schema(self) -> Dict[str, Any]:
        url = f"{self.base_url}/databases/{self.database_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_rollups(self) -> List[Dict[str, Any]]:
        schema = self.get_database_schema()
        properties = schema.get("properties", {})

        rollups = []
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "rollup":
                rollup_info = {
                    "name": prop_name,
                    "id": prop_data.get("id"),
                    "rollup": prop_data.get("rollup", {}),
                }
                rollups.append(rollup_info)

        return rollups

    def post_data(self, data: Dict[str, Any]):
        url = "https://api.notion.com/v1/pages/"
        responses = []
        for item in data:
            response = requests.post(url, json=item, headers=self.headers)
            responses.append(response.json())
        return responses
