import os
import time
import requests
from .constants import Constants

class NewPrint:
    def __init__(self, id):
        self.id = id
    
    @staticmethod
    def test_loki_connection():
        """Test function to verify Loki connectivity and check available labels."""
        loki_url = "http://localhost:3100"
        
        try:
            # Test 1: Check if Loki is reachable
            health_url = f"{loki_url}/ready"
            response = requests.get(health_url, timeout=2)
            print(f"Loki health check: {response.status_code} - {response.text}")
            
            # Test 2: Send a test log entry
            test_payload = {
                "streams": [{
                    "stream": {
                        "job": "test",
                        "test_id": "connection_test",
                    },
                    "values": [[str(int(time.time() * 1e9)), "Test log entry from NewPrint"]]
                }]
            }
            push_response = requests.post(f"{loki_url}/loki/api/v1/push", json=test_payload, timeout=2)
            print(f"Test push response: {push_response.status_code}")
            if push_response.status_code != 204:
                print(f"Error: {push_response.text}")
            
            # Test 3: Query labels (this is what Grafana uses)
            labels_url = f"{loki_url}/loki/api/v1/labels"
            labels_response = requests.get(labels_url, timeout=2)
            if labels_response.status_code == 200:
                labels_data = labels_response.json()
                print(f"Available labels in Loki: {labels_data.get('data', [])}")
            else:
                print(f"Failed to fetch labels: {labels_response.status_code} - {labels_response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Failed to connect to Loki: {e}")
            print("Make sure Loki is running at http://localhost:3100")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def newprint(self, *msgs, end="\n", event="log", skipconsole=False, level="info"):
        # timestamp in [] and id in [] then only message
        # allow multiple message parts (e.g. self.newprint("text", videoId))
        # Check if USE_GRAFANA env variable exists. If not, just print and return.
        msg = " ".join(str(m) for m in msgs) if msgs else ""
        # ensure end is a string or None
        if end is not None and not isinstance(end, str):
            end = str(end)

        lokiline = f"[{self.id}] {msg}"
        logtime = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
        line = logtime + lokiline
        if not os.environ.get("USE_GRAFANA"):
            print(line, end=end)
            return
        print(line, end=end) if not skipconsole else None

        # Stream the same log line to a local Loki instance at port 3100
        # Requires "USE_GRAFANA" environment variable to be set to True
        try:
            loki_url = "http://localhost:3100/loki/api/v1/push"
            # Loki expects nanosecond epoch as a string
            timestamp_ns = str(int(time.time() * 1e9))
            # include the printed end (if any) in the log line sent to Loki
            send_line = lokiline + (end if end is not None else "")
            
            # Ensure all label values are strings (Loki requirement)
            # Use lowercase label names (Loki best practice)
            stream_labels = {
                "job": "consumer",
                "consumer_id": str(self.id),
                "event": str(event),
                "level": str(level),
                "session": str(Constants.SESSION),
            }
            
            payload = {
                "streams": [
                    {
                        "stream": stream_labels,
                        "values": [[timestamp_ns, send_line]],
                    }
                ]
            }
            
            # Debug: Print payload if DEBUG_LOKI env var is set
            if os.environ.get("DEBUG_LOKI"):
                print(f"[DEBUG] Sending to Loki - Labels: {stream_labels}")
            
            # Send to Loki with proper error handling
            response = requests.post(loki_url, json=payload, timeout=2)
            
            # Check if the request was successful
            if response.status_code != 204:
                # Log error but don't crash the app
                error_msg = f"Loki push failed: {response.status_code} - {response.text}"
                print(f"[ERROR] {error_msg}", end=end)
                # Try to send error to Loki with a different label set
                try:
                    error_payload = {
                        "streams": [{
                            "stream": {
                                "job": "loki_error",
                                "consumer_id": str(self.id),
                            },
                            "values": [[str(int(time.time() * 1e9)), error_msg]]
                        }]
                    }
                    requests.post(loki_url, json=error_payload, timeout=1)
                except Exception:
                    pass  # Ignore errors when logging errors
        except requests.exceptions.RequestException as e:
            # Network/connection errors
            print(f"[ERROR] Failed to connect to Loki: {e}", end=end)
        except Exception as e:
            # Other unexpected errors
            print(f"[ERROR] Unexpected error sending to Loki: {e}", end=end)