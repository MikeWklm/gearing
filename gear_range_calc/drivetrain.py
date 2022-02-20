"""Construct a Bike Drivetrain with some plotting utils."""
import math
from dataclasses import InitVar, dataclass, field
from functools import cached_property
from typing import List, Tuple, Union

import pandas as pd
import plotly.graph_objects as go

HOVERTEMPLATE = 'Speed: {speed:.1f} km/h<br>RPM: {rpm:.0f}<br>Chain Cog: {chain_cog:.0f}<br>Casette Cog: {casette_cog:.0f}<br>Ratio: {ratio:.2f}<br>Unfolding: {unfolding:.2f} m'
MARKER_COLOR = {0: 'rgba(0,102,153,1)', 1: 'rgba(204,102,153,1)'}
LINE_COLOR = {0: 'rgba(0,102,153,0.7)', 1: 'rgba(204,102,153,0.7)'}
LINDE_WIDTH = {0: 50, 1: 70}
MARKER_SIZE = {0: 40, 1: 60}
MARKER_WIDTH = {0: 6, 1: 6}


@dataclass
class Casette:
    """A Casette of n cogs."""
    n_speed: int = field(init=False)
    cogs: List[int]

    def __post_init__(self):
        self.n_by = len(self.cogs)


@dataclass
class Chainring:
    """A Chainring of n cogs."""
    n_by: int = field(init=False)
    cogs: List[int]

    def __post_init__(self):
        self.n_by = len(self.cogs)

    def __mul__(self, other: Casette) -> pd.DataFrame:
        """Multiply behavior for chainring.
        
        Should only work with a Casette and gives
        the ratios of all possible combinations.

        Args:
            other (Casette): cassette to multiply with

        Returns:
            pd.DataFrame: all possible gear ratios
        """
        assert isinstance(
            other, Casette), 'can only be multiplied by a Casette'
        ratios = {'chain_cog': list(), 'casette_cog': list(), 'ratio': list()}
        for chain_cog in self.cogs:
            for casette_cog in other.cogs:
                ratios['chain_cog'].append(chain_cog)
                ratios['casette_cog'].append(casette_cog)
                ratios['ratio'].append(chain_cog / casette_cog)
        return pd.DataFrame(ratios)

    def __rmul__(self, other) -> pd.DataFrame:
        return self.__mul__(other)


@dataclass
class Wheel:
    """A Wheel with a specific diameter in mm."""
    diameter: float
    tyre_offset: InitVar[float] = 20
    perimeter: float = field(init=False)

    def __post_init__(self, tyre_offset):
        """Calculate real diameter with tyre offset and perimeter.

        Args:
            tyre_offset (float): the tyre offset
        """
        self.diameter = self.diameter + (tyre_offset * 2)
        self.perimeter = self.diameter * math.pi


@dataclass
class Drivetrain:
    """A complete drivetrain."""
    chainring: Chainring
    casette: Casette
    wheel: Wheel

    @classmethod
    def from_numbers(cls, chainring: List[int], casette: List[int], wheel: Tuple[float, float]):
        """Create a Drivetrain from numbers instead of classes.

        Args:
            chainring (List[int]): chainring cogs
            casette (List[int]): casette cogs
            wheel (float): wheel diameter and offset

        Returns:
            Drivetrain: Drivetrain instance
        """
        chainring = Chainring(sorted(chainring))
        casette = Casette(sorted(casette))
        wheel = Wheel(wheel)
        return cls(chainring, casette, wheel)

    @cached_property
    def ratio(self) -> pd.DataFrame:
        """Ratio for all chainring/cassette combinations."""
        return self.chainring * self.casette

    @cached_property
    def unfolding(self) -> pd.DataFrame:
        """unfolding in meters for all chainring/cassette combinations."""
        ratio = self.ratio
        ratio['unfolding'] = ratio['ratio'] * self.wheel.perimeter / 1000
        return ratio

    def speed(self, rpm: Union[int, Tuple[int, int]]) -> pd.DataFrame:
        """Speed in km/h  for all chainring/cassette combinations.

        Args:
            rpm (Union[int, Tuple[int, int]]): rpm, if tuple a range of lower,
            middle (autocalc) and upper is calculated

        Returns:
            pd.DataFrame: result DataFrame
        """
        speed = self.unfolding
        if isinstance(rpm, int):
            rpm = (rpm,)
        assert len(rpm) <= 2, 'rpm needs to be int or tuple of two ints'
        rpm = sorted(rpm)
        if len(rpm) == 2:
            lower, upper = rpm
            rpm = (lower, lower + ((upper - lower) / 2), upper)
        for rpm, suffix in zip(rpm, ('_lower', '_middle', '_upper')):
            speed['speed'+suffix] = speed['unfolding'] * rpm / 60 * 3.6
            speed['rpm'+suffix] = rpm
        speed['tyre_diameter'] = self.wheel.diameter
        return speed

    def plot_gear_range(self, rpm: Tuple[int, int]) -> go.Figure:
        """Plot the gear range for a given rpm range.

        Args:
            rpm (Tuple[int, int]): rpm range

        Returns:
            go.Figure: the gear range figure
        """
        scatters = list()
        for idx, row in self.speed(rpm).iterrows():
            scatters.append(self._get_trace(row, idx))
        fig = go.Figure()
        fig.add_traces(scatters)
        fig.update_layout(template='plotly_white',
                          showlegend=False,
                          scene=dict(
                              xaxis=dict(showticklabels=False),
                              yaxis=dict(showticklabels=False),
                          ),
                          xaxis={'title': 'Speed in km/h', 'tickmode': 'linear', 'tick0': 5, 'dtick': 5},
                          yaxis={'title': 'Chain Cog'})
        fig.update_xaxes(range=[5,60])
        return fig

    @staticmethod
    def _get_trace(row: pd.Series, switch: int):
        """Generate a Scatter trace for a row of the gearing range frame.

        Args:
            row (pd.Series): row from gearing range frame
            switch (int): switch state for color changing

        Returns:
            go.Scatter: a scatter trace
        """
        speeds = (row.speed_lower, row.speed_middle, row.speed_upper)
        cogs = (str(int(row.chain_cog)),) * len(speeds)
        rpms = (row.rpm_lower, row.rpm_middle, row.rpm_upper)

        hovertext = list()
        for speed, rpm in zip(speeds, rpms):
            hovertext.append(HOVERTEMPLATE.format(speed=speed, rpm=rpm, chain_cog=row.chain_cog,
                             casette_cog=row.casette_cog, ratio=row.ratio, unfolding=row.unfolding))

        switch = switch % 2

        scatter = go.Scatter(x=speeds,
                             y=cogs,
                             marker={'symbol': 'line-ns', 'size': MARKER_SIZE[switch],
                                     'line_color': MARKER_COLOR[switch],
                                     'color': MARKER_COLOR[switch], 'line_width': MARKER_WIDTH[switch]},
                             line={
                                 'width': LINDE_WIDTH[switch], 'color': LINE_COLOR[switch]},
                             text=hovertext,
                             hoverinfo='text',
                             showlegend=False)
        return scatter
