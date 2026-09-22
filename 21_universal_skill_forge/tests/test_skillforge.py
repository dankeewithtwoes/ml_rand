import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skill import Skill, SkillError, SkillValidationError, discover_skills
from skillforge import TEMPLATE, create_skill, test_skill as run_examples


class SkillForgeTests(unittest.TestCase):
    def test_discovery_ignores_empty_directories(self):
        names = [skill.name for skill in discover_skills(ROOT / "skills")]
        self.assertIn("calculator", names)
        self.assertNotIn("search", names)

    def test_calculator_examples(self):
        result = run_examples(Skill(ROOT / "skills" / "calculator"))
        self.assertTrue(result["passed"])
        self.assertEqual(2, len(result["cases"]))

    def test_schema_is_strict(self):
        skill = Skill(ROOT / "skills" / "calculator")
        with self.assertRaises(SkillValidationError): skill.run({"expression": 4})
        with self.assertRaises(SkillValidationError): skill.run({"expression": "2+2", "secret": "nope"})

    def test_calculator_rejects_code_execution(self):
        with self.assertRaises(SkillError):
            Skill(ROOT / "skills" / "calculator").run({"expression": "__import__('os').getcwd()"})

    def test_scaffold_contract_and_overwrite_guard(self):
        self.assertEqual({"manifest.json", "schema.json", "handler.py", "examples.json"}, set(TEMPLATE))
        with self.assertRaises(SkillError):
            create_skill("existing", ROOT / "tests" / "fixtures")

    def test_malformed_manifest_has_actionable_error(self):
        with self.assertRaisesRegex(SkillValidationError, "name must"):
            Skill(ROOT / "tests" / "fixtures" / "malformed")


if __name__ == "__main__":
    unittest.main()
