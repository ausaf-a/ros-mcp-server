import socket
import json
import websocket
import base64
import time

class WebSocketManager:
    def __init__(self, ip: str, port: int, local_ip: str):
        self.ip = ip
        self.port = port
        self.local_ip = local_ip
        self.ws = None

    @property
    def connected(self):
        """Check if WebSocket is connected"""
        return self.ws is not None and self.ws.connected

    def connect(self):
        if self.ws is None or not self.ws.connected:
            sock = socket.create_connection((self.ip, self.port), source_address=(self.local_ip, 0))
            ws = websocket.WebSocket()
            ws.sock = sock
            ws.connect(f"ws://{self.ip}:{self.port}")
            self.ws = ws
            print("[WebSocket] Connected")

    def send(self, message: dict):
        self.connect()
        if self.ws:
            try:
                # Ensure message is JSON serializable
                json_msg = json.dumps(message)
                self.ws.send(json_msg)
                print(f"[WebSocket] Sent: {json_msg[:100]}...")
            except TypeError as e:
                print(f"[WebSocket] JSON serialization error: {e}")
                self.close()
            except Exception as e:
                print(f"[WebSocket] Send error: {e}")
                self.close()

    def send_message(self, message):
        """Alias for send() method for compatibility"""
        if isinstance(message, str):
            try:
                message_dict = json.loads(message)
                return self.send(message_dict)
            except json.JSONDecodeError:
                print(f"[WebSocket] Invalid JSON string: {message}")
                return
        return self.send(message)

    def receive_service_response(self, timeout=5.0) -> str:
        """Receive service response (for get_topics, etc.)"""
        self.connect()
        if self.ws:
            try:
                # Set socket timeout
                self.ws.sock.settimeout(timeout)
                
                # For service responses, we expect a quick response
                for attempt in range(5):
                    try:
                        raw = self.ws.recv()
                        print(f"[WebSocket] Service response (attempt {attempt + 1}): {raw[:200]}...")
                        
                        if raw:
                            # For service responses, return immediately
                            return raw
                            
                        time.sleep(0.2)  # Small delay between attempts
                        
                    except websocket.WebSocketTimeoutException:
                        print(f"[WebSocket] Service timeout on attempt {attempt + 1}")
                        continue
                    except Exception as e:
                        print(f"[WebSocket] Service receive error on attempt {attempt + 1}: {e}")
                        break
                        
            except Exception as e:
                print(f"[WebSocket] General service receive error: {e}")
                self.close()
        return ""

    def receive_binary(self, timeout=3.0) -> bytes:
        """Receive topic subscription data (for joint states, etc.)"""
        self.connect()
        if self.ws:
            try:
                # Set socket timeout
                self.ws.sock.settimeout(timeout)
                
                # Try to receive multiple times to get actual topic data
                for attempt in range(10):  # Try up to 10 times
                    try:
                        raw = self.ws.recv()
                        print(f"[WebSocket] Topic data (attempt {attempt + 1}): {raw[:200]}...")
                        
                        # Parse the message to see if it's actual topic data
                        if raw:
                            data = json.loads(raw)
                            # Look for actual topic message (not just subscription confirmation)
                            if "msg" in data and data.get("topic") == "/joint_states":
                                return raw.encode() if isinstance(raw, str) else raw
                            elif "op" in data and data["op"] == "publish":
                                return raw.encode() if isinstance(raw, str) else raw
                            
                        time.sleep(0.1)  # Small delay between attempts
                        
                    except websocket.WebSocketTimeoutException:
                        print(f"[WebSocket] Topic timeout on attempt {attempt + 1}")
                        continue
                    except Exception as e:
                        print(f"[WebSocket] Topic receive error on attempt {attempt + 1}: {e}")
                        break
                        
            except Exception as e:
                print(f"[WebSocket] General topic receive error: {e}")
                self.close()
        return b""
    
    def get_topics(self) -> list[tuple[str, str]]:
        self.connect()
        if self.ws:
            try:
                print("[WebSocket] Requesting topics list...")
                self.send({
                    "op": "call_service",
                    "service": "/rosapi/topics",
                    "id": "get_topics_request_1"
                })
                
                # Use the dedicated service response method
                response = self.receive_service_response(timeout=10.0)
                print(f"[WebSocket] Topics service response: {response[:300]}...")
                
                if response:
                    data = json.loads(response)
                    if "values" in data:
                        topics = data["values"].get("topics", [])
                        types = data["values"].get("types", [])
                        if topics and types and len(topics) == len(types):
                            print(f"[WebSocket] Found {len(topics)} topics")
                            return list(zip(topics, types))
                        else:
                            print("[WebSocket] Mismatch in topics and types length")
                    else:
                        print(f"[WebSocket] No 'values' in response: {data}")
                else:
                    print("[WebSocket] No response received for topics request")
                    
            except json.JSONDecodeError as e:
                print(f"[WebSocket] JSON decode error: {e}")
                print(f"[WebSocket] Raw response was: {response}")
            except Exception as e:
                print(f"[WebSocket] Topics request error: {e}")
        return []

    def close(self):
        if self.ws and self.ws.connected:
            try:
                self.ws.close()
                print("[WebSocket] Closed")
            except Exception as e:
                print(f"[WebSocket] Close error: {e}")
            finally:
                self.ws = None
