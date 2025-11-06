import asyncio
import redis.asyncio as aioredis
import json
class EventBus:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()

    async def publish(self, channel: str, message: dict):
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str, handler):
        await self.pubsub.subscribe(channel)
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                await handler(json.loads(message["data"]))
