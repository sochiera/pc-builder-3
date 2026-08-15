import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class VerificationProfilesTest(unittest.TestCase):
    def test_smoke_then_hardware_publishes_both_results(self):
        results = []
        for profile in ("smoke", "hardware"):
            try:
                result = subprocess.run(
                    ["timeout", "120", "make", profile],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                self.fail(f"{profile} exceeded the 120 second verification timeout: {error}")
            results.append((profile, result))

        for profile, result in results:
            output = result.stdout + result.stderr
            profile_output = f"profile={profile}\n{output}"
            with self.subTest(profile=profile, assertion="exit code"):
                self.assertEqual(result.returncode, 0, output)
            with self.subTest(profile=profile, assertion="command publication"):
                self.assertRegex(profile_output, r"(?is)\bcommand\b.*unittest")
            with self.subTest(profile=profile, assertion="numeric result publication"):
                self.assertRegex(profile_output, r"(?is)\brc\s*=\s*0\b")


    def test_failed_profile_publishes_nonzero_result(self):
        result = subprocess.run(
            [
                "make",
                "smoke",
                'PROFILE_TESTS=python3 -c "import sys; sys.exit(7)"',
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout + result.stderr

        self.assertNotEqual(result.returncode, 0, output)
        self.assertRegex(output, r"(?is)profile=smoke\s+rc=7\b")


if __name__ == "__main__":
    unittest.main()
