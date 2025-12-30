import asyncio
import time

from telethon import events
from utils.config import get_http_session


WEATHER_SPIN_FRAMES = ["🌸✨", "🌸💖", "🌸🌈", "🌸💫", "🍥✨", "🔮✨"]


async def _fetch_weather(city: str):
    session = await get_http_session()

    urls = [
        f"https://wttr.in/{city}?format=j1",
        f"http://wttr.in/{city}?format=j1",
    ]

    last_error = None
    for url in urls:
        try:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.json()
                last_error = f"HTTP {resp.status}"
        except Exception as e:
            last_error = str(e)

    raise RuntimeError(last_error or "Failed to fetch weather data")


def register(app):

    @app.on(events.NewMessage(pattern=r"\.weather(?:\s+(.*))?$", outgoing=True))
    async def weather_info(event):
        city = (event.pattern_match.group(1) or "").strip()
        if not city:
            return await event.edit("Provide city name. Example: `.weather jakarta`")

        spinner_running = True

        async def spinner(msg):
            i = 0
            try:
                while spinner_running:
                    frame = WEATHER_SPIN_FRAMES[i % len(WEATHER_SPIN_FRAMES)]
                    try:
                        await msg.edit(
                            f"{frame}  Fetching weather for **{city.title()}**...\nPlease wait..."
                        )
                    except Exception:
                        pass
                    i += 1
                    await asyncio.sleep(0.6)
            except asyncio.CancelledError:
                pass

        status_msg = await event.edit(f"🌤 Fetching weather for **{city.title()}**...")
        spin_task = asyncio.create_task(spinner(status_msg))

        try:
            data = await _fetch_weather(city)

            current = data.get("current_condition", [{}])[0]
            weather_desc = current.get("weatherDesc", [{"value": "N/A"}])[0].get("value", "N/A")
            temp_c = current.get("temp_C", "N/A")
            feels = current.get("FeelsLikeC", "N/A")
            humidity = current.get("humidity", "N/A")
            wind = f"{current.get('windspeedKmph', 'N/A')} km/h ({current.get('winddir16Point', 'N/A')})"
            cloud = current.get("cloudcover", "N/A")

            astronomy = data.get("weather", [{}])[0].get("astronomy", [{}])[0]
            sunrise = astronomy.get("sunrise", "N/A")
            sunset = astronomy.get("sunset", "N/A")

            report = (
                f"🌤 **Weather — {city.title()}**\n\n"
                f"🔎 Condition : {weather_desc}\n"
                f"🌡 Temperature: {temp_c}°C (Feels like {feels}°C)\n"
                f"💧 Humidity: {humidity}%\n"
                f"💨 Wind: {wind}\n"
                f"☁️ Cloud Cover: {cloud}%\n\n"
                f"🌅 Sunrise: {sunrise}\n"
                f"🌇 Sunset : {sunset}\n\n"
                f"📅 Fetched: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}"
            )

            spinner_running = False
            spin_task.cancel()
            await status_msg.edit(report)

        except asyncio.TimeoutError:
            spinner_running = False
            spin_task.cancel()
            await status_msg.edit("Request timed out. Try again later.")
        except Exception as e:
            spinner_running = False
            spin_task.cancel()
            await status_msg.edit(f"Couldn't fetch weather data.\nError: {e}")
            