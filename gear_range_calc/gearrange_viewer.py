"""Tiny Streamlit App for a Gear Calculation Frontend."""
from email.policy import default
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from drivetrain import Casette, Chainring, Drivetrain, Wheel
from preconfigs import ALL_OPTIONS, ALL_OPTIONS_NAMES

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
        chainring_cogs = ', '.join([str(cog) for cog in drivetrain.chainring.cogs])
        casette_cogs = ', '.join([str(cog) for cog in drivetrain.casette.cogs])
        st.markdown(f' RPM Range [{lower}, {upper}] | '
                    f'Wheel Diameter: {drivetrain.wheel.diameter:.0f} mm | '
                    f'Chainring: [{chainring_cogs}] | '
                    f'Casette: [{casette_cogs}]')
        st.plotly_chart(drivetrain.plot_gear_range(
            dt['rpms']), use_container_width=True)


st.subheader(f'Configure your Drivetrains.')
# get inputs inside a form (batch input)
with st.form(key='gear_range_form'):
    name = st.text_input(label='Configuration Name',
                         value=f'Configuration 1',
                         max_chars=100)

    a, b, c = st.columns([1, 1, 3])
    chainring = a.multiselect(label='Chainring Range',
                              options=list(range(24, 52)),
                              default=[40])
    casette_preconf = b.selectbox(label='Preconfigured Casette',
                                  options=ALL_OPTIONS_NAMES,)
    casette_cstm = c.multiselect(label='Custom Casette',
                                 options=list(range(9, 50)),
                                 default=[10, 11, 12, 13, 14, 15, 17, 19, 22, 26, 32, 38, 44])

    d, e, f = st.columns(3)
    tyre = d.slider(label='Rim Diameter [mm]',
                    min_value=500, max_value=800, value=700, step=1)

    tyre_offset = e.slider(label='Tyre Offset [mm]',
                           help='The tyre makes the actual diameter of the wheel bigger. We need to account for that.',
                           min_value=5, max_value=50, value=20, step=1)

    rpms = f.select_slider(label='Cadence Range [rpm]',
                           options=list(range(60, 120)),
                           value=(85, 95))
    add = st.form_submit_button('Add Configuration')

if add:
    # construct the drivetrain
    chainring = Chainring(sorted(chainring))
    if casette_preconf == 'CUSTOM':
        casette = casette_cstm
    else:
        casette = ALL_OPTIONS[casette_preconf]
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
