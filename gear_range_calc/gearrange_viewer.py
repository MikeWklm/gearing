"""Tiny Streamlit App for a Gear Calculation Frontend."""
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from drivetrain import Casette, Chainring, Drivetrain, Wheel

st.set_page_config(layout="wide")

st.title('Gear Range Calculator.')

# init a session state
if 'drivetrains' not in st.session_state:
    st.session_state.drivetrains = dict()

# setup util function
def remove_drivetrain(to_exclude: List[str]) -> None:
    """Utility function to remove a drivetrain from session."""
    for dt in to_exclude:
        del st.session_state.drivetrains[dt]
        
@st.cache
def get_current_rawdata(cache: Dict[str, Dict[str, Any]]) -> 'path_or_buf':
    """Utility function to get the current used rawdata."""
    all_drivetrains = list()
    for name, dt in cache.items():
        df_dt = dt['drivetrain'].speed(dt['rpms'])
        df_dt['configuration'] = name
        all_drivetrains.append(df_dt)
    if not all_drivetrains:
        return pd.DataFrame().to_csv().encode('utf-8')
    return pd.concat(all_drivetrains).to_csv().encode('utf-8')


def plot_configs() -> None:
    """Utility function to plat a drivetrain configuration."""
    for n, dt in st.session_state.drivetrains.items():
        lower, upper = dt['rpms']
        drivetrain: Drivetrain = dt['drivetrain']
        st.subheader(f'Gear Range for {n}')
        st.markdown(f' RPM Range [{lower}, {upper}], Wheel Diameter: {drivetrain.wheel.diameter:.0f} mm')
        st.plotly_chart(drivetrain.plot_gear_range(
            dt['rpms']), use_container_width=True)

st.subheader(f'Configure your Drivetrains.')
# get inputs inside a form (batch input)
with st.form(key='gear_range_form'):
    name = st.text_input(label='Name of your configuration.',
                         value=f'Configuration 1',
                         max_chars=100)

    a, b = st.columns([1, 3])
    chainring = a.multiselect(label='Chainring range',
                              options=list(range(24, 52)),
                              default=[40])
    casette = b.multiselect(label='Casette range',
                            options=list(range(9, 50)),
                            default=[10, 11, 12, 13, 14, 15, 17, 19, 22, 26, 32, 38, 44])

    c, d, e = st.columns(3)
    tyre = c.slider(label='Rim diameter [mm]',
                    min_value=500, max_value=800, value=700, step=1)

    tyre_offset = d.slider(label='Tyre offset [mm]',
                           help='The tyre makes the actual diameter of the wheel bigger. We need to account for that.',
                           min_value=5, max_value=50, value=20, step=1)

    rpms = e.select_slider(label='Cadence range [rpm]',
                           options=list(range(60, 120)),
                           value=(85, 95))
    add = st.form_submit_button('Add Configuration')    

if add:
    # construct the drivetrain
    chainring = Chainring(sorted(chainring))
    casette = Casette(sorted(casette))
    wheel = Wheel(tyre, tyre_offset)
    drivetrain = Drivetrain(chainring, casette, wheel)

    # add new drivetrain to session
    st.session_state.drivetrains[name] = {'drivetrain': drivetrain,
                                          'rpms': rpms}

st.subheader('Your current Drivetrains:')
# allow user to delete drivetrains
with st.form(key='update_config'):
    current_configs = [k for k, v in st.session_state.drivetrains.items()]
    to_keep = st.multiselect(label='Drivetrains to keep',
                                options=current_configs,
                                default=current_configs)
    update = st.form_submit_button('Update Drivetrains')

# update drivetrains
if update:
    remove_drivetrain(set(current_configs) - set(to_keep))
    
st.subheader('Drivetrain Plots:')
with st.expander('Calculate the Plots for all Drivetrains.'):
    # plot the drivetrains
    plot_configs()

st.download_button('Download Data.', get_current_rawdata(st.session_state.drivetrains), 
                   file_name='gear-range-calculator-data.csv', mime='text/csv')
