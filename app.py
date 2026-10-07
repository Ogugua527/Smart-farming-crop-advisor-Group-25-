from datetime import date

import streamlit as st

from farming_advisor.crops import CROPS
from farming_advisor.recommendations import make_recommendation
from farming_advisor.storage import ALLOWED_ACTIVITIES, add_activity, delete_activity, load_activities
from farming_advisor.weather import WeatherLookupError, get_weather, weather_description


st.set_page_config(page_title="Crop Planting Advisor", page_icon="🌱")
st.title("Crop planting advisor")
st.write("Check the weather for your area and keep a record of farm activities.")

advice_tab, log_tab = st.tabs(["Planting advice", "Farm log"])

with advice_tab:
    st.subheader("Check your local conditions")
    with st.form("weather_form"):
        location = st.text_input("Location", placeholder="Town, district, or city", max_chars=80)
        crop_name = st.selectbox("Crop", list(CROPS))
        check_weather = st.form_submit_button("Check weather")

    if check_weather:
        try:
            st.session_state["weather"] = get_weather(location)
        except ValueError as error:
            st.error(str(error))
        except WeatherLookupError as error:
            st.error(str(error))

    crop = CROPS[crop_name]
    st.caption(f"Preferred temperature: {crop.min_temperature}-{crop.max_temperature} C. Water need: {crop.water_need}.")

    weather = st.session_state.get("weather")
    if weather:
        advice = make_recommendation(crop_name, weather["temperature_c"], weather["precipitation_mm"])
        st.subheader(weather["place"] or "Selected location")
        st.write(weather_description(weather["weather_code"]))
        st.metric("Current temperature", f"{weather['temperature_c']:.1f} C")
        st.metric("Rain forecast for today", f"{weather['precipitation_mm']:.1f} mm")
        st.info(advice["summary"])
        for warning in advice["warnings"]:
            st.warning(warning)
        st.caption(advice["disclaimer"])
    else:
        st.info("Enter a location and check the weather to see a recommendation.")

with log_tab:
    st.subheader("Record a farm activity")
    with st.form("activity_form", clear_on_submit=True):
        activity = st.selectbox("Activity", sorted(ALLOWED_ACTIVITIES))
        activity_crop = st.selectbox("Crop", list(CROPS), key="activity_crop")
        activity_date = st.date_input("Date", value=date.today())
        notes = st.text_input("Notes (optional)", max_chars=500)
        save_activity = st.form_submit_button("Save activity")

    if save_activity:
        try:
            add_activity(activity, activity_crop, activity_date, notes)
            st.success("Activity saved.")
        except ValueError as error:
            st.error(str(error))

    st.subheader("Saved activities")
    try:
        records = sorted(load_activities(), key=lambda item: item.get("date", ""), reverse=True)
        if not records:
            st.caption("No activities recorded yet.")
        for record in records:
            record_title = f"{record.get('date', 'Unknown date')} · {record.get('activity', 'Activity')} · {record.get('crop', 'Crop')}"
            first_column, second_column = st.columns([5, 1])
            first_column.write(record_title)
            if record.get("notes"):
                first_column.caption(record["notes"])
            if record.get("id") and second_column.button("Delete", key=f"delete_{record['id']}"):
                delete_activity(record["id"])
                st.rerun()
    except ValueError as error:
        st.error(str(error))
