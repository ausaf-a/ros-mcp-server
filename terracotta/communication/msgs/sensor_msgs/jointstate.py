from typing import List, Any, Protocol

class Publisher(Protocol):
    def send(self, message: dict) -> None:
        ...

class JointState:
    def __init__(self, publisher: Publisher, topic: str = "/joint_states"):
        self.publisher = publisher
        self.topic = topic

    def publish(self, name: List[str], position: List[float], velocity: List[float], effort: List[float]):
        msg = {
            "op": "publish",
            "topic": self.topic,
            "msg": {
                "header": {},
                "name": name,
                "position": position,
                "velocity": velocity,
                "effort": effort
            }
        }
        self.publisher.send(msg)
        return msg

    def subscribe(self, timeout=5.0):
        """Subscribe to joint states with improved error handling"""
        print(f"[JointState] Subscribing to {self.topic}")
        
        subscribe_msg = {
            "op": "subscribe",
            "topic": self.topic,
            "type": "sensor_msgs/msg/JointState"
        }
        
        try:
            self.publisher.send(subscribe_msg)
            print(f"[JointState] Sent subscription request")
            
            raw = self.publisher.receive_binary(timeout)
            if not raw:
                print(f"[JointState] No data received within {timeout} seconds")
                return None
                
            # Handle both bytes and string
            if isinstance(raw, bytes):
                raw_str = raw.decode('utf-8')
            else:
                raw_str = raw
                
            print(f"[JointState] Raw response: {raw_str[:200]}...")
            
            import json
            msg = json.loads(raw_str)
            
            # Extract the actual message data
            if "msg" in msg:
                joint_data = msg["msg"]
                print(f"[JointState] Successfully parsed joint state data")
                return joint_data
            else:
                print(f"[JointState] No 'msg' field in response: {msg}")
                return msg
                
        except json.JSONDecodeError as e:
            print(f"[JointState] JSON decode error: {e}")
            print(f"[JointState] Raw data was: {raw}")
            return None
        except Exception as e:
            print(f"[JointState] Subscription error: {e}")
            return None
