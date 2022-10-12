import os
import asyncio
import time

from aiohttp import ClientSession

from forum_scraper import ForumScraper


thread = os.environ["THREAD_URL"]
cookie = os.environ["FORUM_COOKIE"]
vercel = os.environ["VERCEL_URL"]
api_token = os.environ["API_TOKEN"]

payload = {
    "key": api_token,
    "prompt": "",
    "seed": 12347,
    "steps": 30
}

scraper = ForumScraper(thread, cookie)

async def fetch(data, session):
    payload["prompt"] = data["phrase"]
    async with session.post(vercel, json=payload) as response:
        if response.status > 200:
            return data
        res = await response.json()
        if "ok" in res and res["ok"]:
            data["img"] = res["image_url"]
            return data
        return data
            
async def get_image(users_data):
    tasks = []
    async with ClientSession() as session:
        for i in users_data:
            task = fetch(i, session)
            tasks.append(task)
        return await asyncio.gather(*tasks)

def main():
    u_data = scraper.get_user_prompts(thread)
    user_responses = asyncio.run(get_image(u_data))
    # print(user_responses)
    for user in user_responses:
        # print(user)
        if "img" in user:
            scraper.reply(user["author"], user["phrase"], user["img"])
        time.sleep(40)
    time.sleep(40)
    main()

try:
    main()
except Exception as e:
    print(e)
    time.sleep(20)
    main()
