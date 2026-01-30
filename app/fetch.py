import httpx
import asyncio
from app.config import ROBOTEVENTS_TOKEN

root = 'https://www.robotevents.com/api/v2'

# Global semaphore to ensure only 1 fetch at a time
_fetch_semaphore = asyncio.Semaphore(1)

async def fetch(target, params):
    async with _fetch_semaphore:  # Only one fetch can proceed at a time
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + ROBOTEVENTS_TOKEN
        }
        page = 1
        output = []

        async with httpx.AsyncClient() as client:
            while True:
                request_params = {**params, "per_page": 250, "page": page}
                endpoint = root + f"/{target}"
                response = await client.get(endpoint, headers=headers, params=request_params)
                data = response.json()
                
                # If no data returned, we've reached the end
                if not data["data"]:
                    break
                
                output.extend(data["data"])
                last_page = data['meta']['last_page']
                print(f"Fetched {target} ({page} of {last_page})")

                if page >= last_page:
                    break

                page += 1
                await asyncio.sleep(1) # Rate limiting
        
        print(f"Fetched {len(output)} {target}")
        return output