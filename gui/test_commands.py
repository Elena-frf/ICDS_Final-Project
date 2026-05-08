#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for chat client functionality
"""
import socket
import json
import time
from chat_utils import mysend, myrecv

def test_client():
    # Connect to server
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 1112))

    print("Connected to server")

    # Login
    login_msg = json.dumps({"action": "login", "name": "TestUser", "password": "test123"})
    mysend(s, login_msg)
    response = json.loads(myrecv(s))
    print(f"Login response: {response}")

    if response.get("status") == "ok":
        print("Login successful")

        # Test time command
        print("\n--- Testing TIME command ---")
        mysend(s, json.dumps({"action": "time"}))
        time_response = json.loads(myrecv(s))
        print(f"Time response: {time_response}")

        # Test who command
        print("\n--- Testing WHO command ---")
        mysend(s, json.dumps({"action": "who"}))
        who_response = json.loads(myrecv(s))
        print(f"Who response: {who_response}")

        # Test list command
        print("\n--- Testing LIST command ---")
        mysend(s, json.dumps({"action": "list"}))
        list_response = json.loads(myrecv(s))
        print(f"List response: {list_response}")

        # Test connect command (will fail since no other users)
        print("\n--- Testing CONNECT command ---")
        mysend(s, json.dumps({"action": "connect", "target": "NonExistentUser"}))
        connect_response = json.loads(myrecv(s))
        print(f"Connect response: {connect_response}")

        print("\n--- Test completed ---")

    s.close()

if __name__ == "__main__":
    test_client()