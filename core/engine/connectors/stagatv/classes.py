class _Article:

    def __init__(self, name: str, season_number: int = None, episode_number: int = None, is_series: bool = True):
        self._name = name
        self._season_number = season_number
        self._episode_number = episode_number
        self._is_series = is_series
