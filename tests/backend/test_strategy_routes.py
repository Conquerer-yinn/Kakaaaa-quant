import unittest

from backend.api.routes import get_chinext_limit_up_event_study
from backend.main import app
from backend.schemas.strategies import StrategyStudyResponse


class StrategyRoutesTest(unittest.TestCase):
    def test_openapi_contains_strategy_read_and_run_routes(self):
        paths = app.openapi()["paths"]

        self.assertIn("/strategies/chinext-limit-up-event-study", paths)
        self.assertIn("get", paths["/strategies/chinext-limit-up-event-study"])
        self.assertIn("/strategies/chinext-limit-up-event-study/run", paths)
        self.assertIn("post", paths["/strategies/chinext-limit-up-event-study/run"])

    def test_read_route_returns_declared_response_model(self):
        response = get_chinext_limit_up_event_study(limit=10)

        self.assertIsInstance(response, StrategyStudyResponse)


if __name__ == "__main__":
    unittest.main()
