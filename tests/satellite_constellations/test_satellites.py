import unittest
import numpy as np
from rubin_sim.utils import survey_start_mjd
from rubin_sim.satellite_constellations import (
    starlink_tles_v1,
    starlink_tles_v2,
    oneweb_tles,
    Constellation,
)


class TestSatellites(unittest.TestCase):
    def test_constellations(self):
        """Test stellite constellations"""

        mjd0 = survey_start_mjd()
        sv1 = starlink_tles_v1()
        sv2 = starlink_tles_v2()
        ow = oneweb_tles()

        const = Constellation(sv1)

        lengths, n_s = const.check_pointings(
            np.array([85.0, 82.0]),
            np.array([0.0, 0.0]),
            np.arange(2) + mjd0 + 1.5,
            30.0,
        )

        assert np.size(lengths) == 2
        assert np.size(n_s) == 2


if __name__ == "__main__":
    unittest.main()
