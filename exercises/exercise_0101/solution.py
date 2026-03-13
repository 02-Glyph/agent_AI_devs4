# exercises/exercise_01/solution.py
import asyncio
from exercises.client import post

async def main():
    result = await post("/verify", {"answer": "42"})
    print(result)

asyncio.run(main())
