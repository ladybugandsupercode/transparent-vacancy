import unittest
from app.source import extract_vacancies


class SourceTests(unittest.TestCase):
    def test_official_shape(self):
        payload = {"results": {"vacancies": [{"vacancy": {"id": "1"}}, {"vacancy": {"id": "2"}}]}}
        self.assertEqual([x["id"] for x in extract_vacancies(payload)], ["1", "2"])

    def test_plain_array(self):
        self.assertEqual(extract_vacancies([{"id": "x"}]), [{"id": "x"}])


if __name__ == "__main__":
    unittest.main()
