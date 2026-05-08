#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for chat client connect functionality
"""
import socket
import json
import time
from chat_utils import mysend, myrecv

def test_connect():
    # Connect to server as User1
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.connect(('127.0.0.1', 1112))

    # Connect to server as User2
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.connect(('127.0.0.1', 1112))

    print("Two clients connected to server")

    # Login as User1
    login_msg1 = json.dumps({"action": "login", "name": "User1", "password": "pass1"})
    mysend(s1, login_msg1)
    response1 = json.loads(myrecv(s1))
    print(f"User1 login response: {response1}")

    # Login as User2
    login_msg2 = json.dumps({"action": "login", "name": "User2", "password": "pass2"})
    mysend(s2, login_msg2)
    response2 = json.loads(myrecv(s2))
    print(f"User2 login response: {response2}")

    if response1.get("status") == "ok" and response2.get("status") == "ok":
        print("Both users logged in successfully")

        # User1 tests who command
        print("\n--- User1 testing WHO command ---")
        mysend(s1, json.dumps({"action": "who"}))
        who_response = json.loads(myrecv(s1))
        print(f"User1 who response: {who_response}")

        # User1 connects to User2
        print("\n--- User1 connecting to User2 ---")
        mysend(s1, json.dumps({"action": "connect", "target": "User2"}))
        connect_response = json.loads(myrecv(s1))
        print(f"User1 connect response: {connect_response}")

        if connect_response.get("status") == "success":
            print("Connection successful!")

            # User2 should receive connect request
            time.sleep(0.1)  # Small delay
            try:
                connect_request = json.loads(myrecv(s2))
                print(f"User2 received: {connect_request}")
            except:
                print("User2 did not receive connect request")

        else:
            print(f"Connection failed: {connect_response}")

    s1.close()
    s2.close()
    print("Test completed")

if __name__ == "__main__":
    test_connect()