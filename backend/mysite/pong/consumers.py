# from channels.generic.websocket import AsyncWebsocketConsumer
# import json

# class PongConsumer(AsyncWebsocketConsumer):
# 	async def connect(self):
# 		await self.accept()

# 	async def disconnect(self, close_code):
# 		pass

# 	async def receive(self, text_data):
# 		text_data_json = json.loads(text_data)
# 		player = text_data_json['player']
# 		movement = text_data_json['movement']

# 		# Send movement to the other player
# 		await self.send(text_data=json.dumps({
# 			'player': player,
# 			'movement': movement
# 		}))

from channels.generic.websocket import AsyncWebsocketConsumer
import json

class PongConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.room_name = self.scope['url_route']['kwargs']['room_name']
		await self.channel_layer.group_add(
			self.room_name,
			self.channel_name
		)

		await self.accept()

	async def disconnect(self, close_code):
		await self.channel_layer.group_discard(
			self.room_name,
			self.channel_name
		)

	async def receive(self, text_data):
		text_data_json = json.loads(text_data)
		player = text_data_json['player']
		movement = text_data_json['movement']

		# Send movement to the other player
		await self.channel_layer.group_send(
			self.room_name,
			{
				'type': 'pong_message',
				'player': player,
				'movement': movement
			}
		)

	async def pong_message(self, event):
		player = event['player']
		movement = event['movement']

		# Send message to WebSocket
		await self.send(text_data=json.dumps({
			'player': player,
			'movement': movement
		}))