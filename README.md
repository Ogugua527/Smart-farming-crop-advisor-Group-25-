# Smart Farming & Crop Planting Advisor

A beginner-friendly Python and Streamlit app for basic planting guidance for maize, rice, tomato, and cassava. It looks up a place with Open-Meteo, shows current conditions and today's precipitation forecast, applies transparent crop-specific rules, and stores farm activity records locally as JSON.

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Start the dashboard with `streamlit run app.py`.

Weather lookup requires an internet connection. No API key is needed. The first saved activity creates `data/activities.json` automatically.

## Test

Run `pytest` from the project root. Recommendation and storage tests do not require internet access.

## Advisory limits

Recommendations use the current temperature and a one-day precipitation forecast. They do not account for seasonal rainfall, soil, variety, pests, or local agricultural guidance, and should not be treated as a substitute for expert advice.
