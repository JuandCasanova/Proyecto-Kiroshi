import unittest

from interfaces.hud.object_descriptions import describe_object
from interfaces.hud.object_scanner import ALLOWED_CATEGORIES


class ObjectDescriptionTests(unittest.TestCase):
    def test_common_objects_have_local_descriptions(self) -> None:
        self.assertIn("portatil", describe_object("laptop"))
        self.assertIn("liquidos", describe_object("bottle"))
        self.assertIn("cursor", describe_object("mouse"))
        self.assertIn("teclado", describe_object("keyboard").lower())
        self.assertIn("respaldo", describe_object("chair"))
        self.assertIn("peluche", describe_object("teddy bear"))

    def test_unknown_categories_get_a_truthful_fallback(self) -> None:
        self.assertEqual(
            describe_object("unknown"),
            "Objeto detectado localmente; descripcion general no disponible.",
        )

    def test_desktop_scanner_allows_mouse_and_chair(self) -> None:
        self.assertIn("mouse", ALLOWED_CATEGORIES)
        self.assertIn("chair", ALLOWED_CATEGORIES)


if __name__ == "__main__":
    unittest.main()
