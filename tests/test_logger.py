import unittest

from start import logger


class TestLogger(unittest.TestCase):
    def test_output(self):
        self.assertEqual(
            str(logger.Success("This is a success message", display=False)),
            "\033[32mThis is a success message\033[0m"
        )

    def test_add(self):
        self.assertEqual(
            str(logger.Success("Success:", False) + logger.Info("this is info", False)),
            "\033[32mSuccess:\033[0m\033[36mthis is info\033[0m"
        )

    def test_wrap(self):
        self.assertEqual(
            str(logger.Error("Error:" + logger.Info("this is error", False), False)),
            "\033[31mError:\033[36mthis is error\033[0m"
        )
