import json
import time
import requests

MCP_URL = "https://api.sportspredict.com/api/v1/mcp"
EVENT_ID = "aa5572ec-5930-4d99-b06b-f8966333d172"
LOBBY_ID = "8df8038c-fd2c-4a5f-be4e-0e11d5966c05"


class SportsPredictClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        self._req_id = 0

    def _call(self, method: str, params: dict, _retries: int = 3):
        self._req_id += 1
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": self._req_id}
        for attempt in range(_retries + 1):
            try:
                resp = requests.post(MCP_URL, headers=self.headers, json=payload, timeout=45)
                if resp.status_code == 429 and attempt < _retries:
                    time.sleep(10 * (attempt + 1))   # 10s, 20s, 30s
                    continue
                if resp.status_code in (502, 503, 504) and attempt < _retries:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                for line in resp.content.decode("utf-8").splitlines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if "error" in data:
                            raise RuntimeError(f"MCP error: {data['error']}")
                        return data.get("result")
                raise RuntimeError(f"No data in MCP response: {resp.text[:200]}")
            except requests.exceptions.ConnectionError:
                if attempt < _retries:
                    time.sleep(2 ** attempt)
                    continue
                raise

    def _tool(self, name: str, arguments: dict):
        result = self._call("tools/call", {"name": name, "arguments": arguments})
        if result and "content" in result:
            text = result["content"][0].get("text", "")
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return result

    def list_events(self):
        return self._tool("list_events", {})

    def list_lobbies(self, event_id: str = None):
        args = {"event_id": event_id} if event_id else {}
        return self._tool("list_lobbies", args)

    def list_matches(self, event_id: str = None):
        args = {"event_id": event_id} if event_id else {}
        return self._tool("list_matches", args)

    def list_markets(self, match_id: str, lobby_id: str = LOBBY_ID):
        return self._tool("list_markets", {"match_id": match_id, "lobby_id": lobby_id})

    def list_predictions(self, lobby_id: str = LOBBY_ID):
        return self._tool("list_predictions", {"lobby_id": lobby_id})

    def list_results(self, lobby_id: str = LOBBY_ID):
        return self._tool("list_results", {"lobby_id": lobby_id})

    def submit_prediction(self, market_id: str, probability: int, lobby_id: str = LOBBY_ID):
        return self._tool("submit_prediction", {
            "market_id": market_id,
            "lobby_id": lobby_id,
            "probability": max(1, min(99, probability)),
        })

    def submit_predictions_batch(self, predictions: list[dict], lobby_id: str = LOBBY_ID):
        """predictions: list of {"market_id": ..., "probability": int}"""
        batch = [
            {"market_id": p["market_id"], "lobby_id": lobby_id,
             "probability": max(1, min(99, p["probability"]))}
            for p in predictions
        ]
        return self._tool("submit_predictions_batch", {"predictions": batch})

    def update_prediction(self, prediction_id: str, probability: int):
        return self._tool("update_prediction", {
            "prediction_id": prediction_id,
            "probability": max(1, min(99, probability)),
        })
