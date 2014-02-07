from django.test import TestCase
from django.test.client import Client
import uuid
import json

class ClientAPITest(TestCase):
    def setUp(self):
        self.clientId = uuid.uuid4().hex

    def test_register_client(self):
        c = Client()
        response = c.post("/clients?s=" + self.clientId)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)
        clientFound = False
        for d in data:
            if d['s'] == self.clientId:
                clientFound = True
        self.assertEqual(clientFound, True)

    def test_unregister_client(self):
        c = Client()
        response = c.post("/clients?s=" + self.clientId, { "x" : 1 })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)
        clientFound = False
        for d in data:
            if d['s'] == clientid:
                clientFound = True
        self.assertEqual(clientFound, False)

class MessagingAPITest(TestCase):
    def setUp(self):
        self.clientId = uuid.uuid4().hex
        self.clientId2 = uuid.uuid4().hex
        self.clientId3 = uuid.uuid4().hex

        c = Client()
        response = c.post("/clients?s=" + self.clientId)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        c = Client()
        response = c.post("/clients?s=" + self.clientId2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        c = Client()
        response = c.post("/clients?s=" + self.clientId3)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")


    def test_call_without_client(self):
        c = Client()
        response = c.get("/messages")
        self.assertEqual(response.status_code, 403) # we expect a deny

    def test_call_with_client(self):
        c = Client()
        response = c.get("/messages?s=" + self.clientId)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

    def test_send_message_from_client1_to_client2(self):
        c = Client()
        response = c.post("/messages?s=" + self.clientId, {'r':self.clientId2, 't': 't1', 'd': 'data1'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        # we should find the message in the client2 queue
        response = c.get("/messages?s=" + self.clientId2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json", "fail: " + response.content)

        data = json.loads(response.content)
        dataFound = False
        for d in data:
            if d['t'] == 't1' and d['d'] == 'data1':
                dataFound = True

        self.assertEqual(dataFound, True)

        # we should NOT find the message in the client3 queue
        response = c.get("/messages?s=" + self.clientId3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)
        dataFound = False
        for d in data:
            if d['t'] == 't1' and d['d'] == 'data1':
                dataFound = True

        self.assertEqual(dataFound, False)


