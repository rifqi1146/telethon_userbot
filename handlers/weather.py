import asyncio

from telethon import events
from utils.config import get_http_session


WEATHER_SPIN_FRAMES = ["🌤", "⛅", "🌥", "☁️", "🌦", "🌈"]


def _weather_code_to_text(code: int) -> str:
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return mapping.get(code, "Unknown")


def _wind_dir_from_degrees(deg) -> str:
    if deg is None:
        return "N/A"
    dirs = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    idx = int((float(deg) + 11.25) // 22.5) % 16
    return dirs[idx]


def _format_location(loc: dict) -> str:
    parts = [loc.get("name"), loc.get("admin1"), loc.get("country")]
    return ", ".join(str(x) for x in parts if x)


async def _resolve_location(city: str):
    session = await get_http_session()
    async with session.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=15,
    ) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Geocoding API returned HTTP {resp.status}")
        data = await resp.json()

    results = data.get("results") or []
    if not results:
        raise ValueError("Location not found")

    return results[0]


async def _fetch_weather(city: str):
    location = await _resolve_location(city)
    session = await get_http_session()

    async with session.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "weather_code",
                "cloud_cover",
                "wind_speed_10m",
                "wind_direction_10m",
                "is_day",
            ]),
            "daily": "sunrise,sunset",
            "timezone": "auto",
            "forecast_days": 1,
        },
        timeout=20,
    ) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Weather API returned HTTP {resp.status}")
        data = await resp.json()

    return location, data


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"^[./]weather(?:\s+(.*))?$", outgoing=True))
    async def weather_info(event):
        city = (event.pattern_match.group(1) or "").strip()
        if not city:
            return await event.edit("🌤 Provide a city name. Example: `.weather jakarta`")

        spinner_running = True

        async def spinner(msg):
            i = 0
            try:
                while spinner_running:
                    frame = WEATHER_SPIN_FRAMES[i % len(WEATHER_SPIN_FRAMES)]
                    try:
                        await msg.edit(
                            f"{frame} Fetching weather for **{city.title()}**...\nPlease wait..."
                        )
                    except Exception:
                        pass
                    i += 1
                    await asyncio.sleep(0.8)
            except asyncio.CancelledError:
                pass

        status_msg = await event.edit(f"🌤 Fetching weather for **{city.title()}**...")
        spin_task = asyncio.create_task(spinner(status_msg))

        try:
            location, data = await _fetch_weather(city)

            current = data.get("current", {}) or {}
            current_units = data.get("current_units", {}) or {}
            daily = data.get("daily", {}) or {}

            weather_code = current.get("weather_code")
            weather_desc = _weather_code_to_text(weather_code if weather_code is not None else -1)

            temp = current.get("temperature_2m", "N/A")
            temp_unit = current_units.get("temperature_2m", "°C")

            feels = current.get("apparent_temperature", "N/A")
            feels_unit = current_units.get("apparent_temperature", "°C")

            humidity = current.get("relative_humidity_2m", "N/A")
            humidity_unit = current_units.get("relative_humidity_2m", "%")

            wind_speed = current.get("wind_speed_10m", "N/A")
            wind_speed_unit = current_units.get("wind_speed_10m", "km/h")
            wind_dir_deg = current.get("wind_direction_10m")
            wind_dir = _wind_dir_from_degrees(wind_dir_deg)

            cloud = current.get("cloud_cover", "N/A")
            cloud_unit = current_units.get("cloud_cover", "%")

            sunrise = (daily.get("sunrise") or ["N/A"])[0]
            sunset = (daily.get("sunset") or ["N/A"])[0]

            observed_time = current.get("time", "N/A")
            tz_abbr = data.get("timezone_abbreviation") or data.get("timezone") or "Local"
            location_name = _format_location(location)

            report = (
                f"🌤 **Weather — {location_name}**\n\n"
                f"🔎 Condition: {weather_desc}\n"
                f"🌡 Temperature: {temp}{temp_unit} (Feels like {feels}{feels_unit})\n"
                f"💧 Humidity: {humidity}{humidity_unit}\n"
                f"💨 Wind: {wind_speed} {wind_speed_unit} ({wind_dir})\n"
                f"☁️ Cloud Cover: {cloud}{cloud_unit}\n\n"
                f"🌅 Sunrise: {sunrise}\n"
                f"🌇 Sunset: {sunset}\n\n"
                f"🕒 Observed: {observed_time} ({tz_abbr})"
            )

            spinner_running = False
            spin_task.cancel()
            await status_msg.edit(report)

        except ValueError as e:
            spinner_running = False
            spin_task.cancel()
            await status_msg.edit(f"📍 {e}")
        except asyncio.TimeoutError:
            spinner_running = False
            spin_task.cancel()
            await status_msg.edit("⌛ Request timed out. Try again later.")
        except Exception as e:
            spinner_running = False
            spin_task.cancel()
            await status_msg.edit(f"❌ Couldn't fetch weather data.\nError: {e}")
            