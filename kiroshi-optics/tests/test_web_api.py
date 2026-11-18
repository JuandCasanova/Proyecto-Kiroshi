import unittest

from fastapi import HTTPException

from interfaces.api.main import _analyze_frame


class WebApiTests(unittest.TestCase):
    def test_invalid_jpeg_is_rejected_before_loading_models(self) -> None:
        with self.assertRaises(HTTPException) as error:
            _analyze_frame(b"not-a-jpeg")

        self.assertEqual(error.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
