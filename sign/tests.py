from django.test import TestCase
from django.test.client import Client
import uuid
import json

class ClientAPITest(TestCase):
    def setUp(self):
        self.clientId = uuid.uuid4().hex

    def test_register_client(self):
        c = Client()
        response = c.post("/api/1.0/client?s=" + self.clientId)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)
        self.assertFalse(u'error' in data)

        clientFound = False
        for d in data:
            if d['s'] == self.clientId:
                clientFound = True
        self.assertEqual(clientFound, True)

    def test_unregister_client(self):
        c = Client()
        response = c.post("/api/1.0/client?s=" + self.clientId, { "x" : 1 })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)
        self.assertFalse(u'error' in data)


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
        response = c.post("/api/1.0/client?s=" + self.clientId)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        c = Client()
        response = c.post("/api/1.0/client?s=" + self.clientId2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        c = Client()
        response = c.post("/api/1.0/client?s=" + self.clientId3)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")


    def test_call_without_client(self):
        c = Client()
        response = c.get("/api/1.0/message")
        self.assertEqual(response.status_code, 403) # we expect a deny

    def test_call_with_client(self):
        c = Client()
        response = c.get("/api/1.0/message?s=" + self.clientId)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

    def test_send_message_from_client1_to_client2(self):
        c = Client()
        response = c.post("/api/1.0/message?s=" + self.clientId, {'r':self.clientId2, 't': 't1', 'd': 'data1'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        # we should find the message in the client2 queue
        response = c.get("/api/1.0/message?s=" + self.clientId2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json", "fail: " + response.content)

        data = json.loads(response.content)
        self.assertFalse(u'error' in data)

        dataFound = False
        for d in data:
            if d['t'] == 't1' and d['d'] == 'data1':
                dataFound = True

        self.assertEqual(dataFound, True)

        # we should NOT find the message in the client3 queue
        response = c.get("/api/1.0/message?s=" + self.clientId3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        data = json.loads(response.content)
        self.assertFalse(u'error' in data)

        dataFound = False
        for d in data:
            if d['t'] == 't1' and d['d'] == 'data1':
                dataFound = True

        self.assertEqual(dataFound, False)

from sign.models import Channel, ChannelRelay, Client as SignClient

class ChannelAPITest(TestCase):
    def setUp(self):
        self.clientId = uuid.uuid4().hex

        c = Client()
        response = c.post("/api/1.0/client?s=" + self.clientId)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

    def test_channel_create(self):
        c = Client()
        response = c.post("/api/1.0/channeladd?s="+self.clientId, {'name': 'testchannel'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertFalse(u'error' in data)


        self.assertEqual(data['channel'], Channel.objects.get(master = SignClient.objects.get(externid = self.clientId), name = 'testchannel', status = Channel.STATUS_ALIVE).pk)

    def test_channel_delete(self):
        c = Client()
        response = c.post("/api/1.0/channeladd?s="+self.clientId, {'name': 'testchannel'})
        channelid = json.loads(response.content)['channel']
        self.assertEqual(len(Channel.objects.filter(pk = channelid)), 1)

        response = c.post("/api/1.0/channeldel?s="+self.clientId, {'channel': channelid})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        with self.assertRaises(Channel.DoesNotExist):
            Channel.objects.get(pk = channelid, status=Channel.STATUS_ALIVE)


    def test_channel_list(self):
        c = Client()
        response = c.post("/api/1.0/channeladd?s="+self.clientId, {'name': 'testchannel'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")

        channelid = json.loads(response.content)['channel']
        self.assertEqual(len(Channel.objects.filter(pk = channelid)), 1)

        response = c.get("/api/1.0/channellist?s="+self.clientId)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertFalse(u'error' in data)

        found = False
        for d in data:
            if d['channel'] == channelid and d['channel_name'] == 'testchannel':
                found = True
        self.assertTrue(found)


class ChannelRelayAPITest(TestCase):
    def setUp(self):
        self.clientId = uuid.uuid4().hex

        c = Client()
        response = c.post("/api/1.0/client?s=" + self.clientId)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        self._addChannel()

    def _addChannel(self):
        c = Client()
        response = c.post("/api/1.0/channeladd?s="+self.clientId, {'name': 'testchannel'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertFalse(u'error' in data)

        self.channelid = data['channel']


    def test_channelrelay_create(self):
        c = Client()
        response = c.post("/api/1.0/channelrelayadd?s="+self.clientId, {'channel': self.channelid})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertFalse(u'error' in data)
        found = False
        for k in data:
            if k == self.clientId:
                found = True
        self.assertTrue(found)


    def test_channelrelay_delete(self):
        c = Client()
        response = c.post("/api/1.0/channelrelayadd?s="+self.clientId, {'channel': self.channelid})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        self.assertEqual(len(ChannelRelay.objects.filter(channel = Channel.objects.get(pk = self.channelid), client = SignClient.objects.get(externid = self.clientId))), 1)

        response = c.post("/api/1.0/channelrelaydel?s="+self.clientId)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertFalse(u'error' in data)
        found = False
        for k in data:
            if k == self.clientId:
                found = True
        self.assertTrue(found)



    def test_channelrelay_list(self):
        c = Client()

        response = c.post("/api/1.0/channelrelayadd?s="+self.clientId, {'channel': self.channelid})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")


        response = c.get("/api/1.0/channelrelaylist?s="+self.clientId+"&channel=" + str(self.channelid ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], "application/json")
        data = json.loads(response.content)
        self.assertFalse(u'error' in data)
        found = False
        for k in data:
            if k == self.clientId:
                found = True
        self.assertTrue(found)


