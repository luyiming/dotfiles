import io
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import manage_tools


class MetadataTests(unittest.TestCase):
    def test_parse_os_release(self):
        contents = """
        # comment
        ID=debian
        VERSION_ID="12"
        VERSION_CODENAME='bookworm'
        """

        self.assertEqual(
            manage_tools.parse_os_release(contents),
            {
                "ID": "debian",
                "VERSION_ID": "12",
                "VERSION_CODENAME": "bookworm",
            },
        )

    def test_compare_versions_pads_missing_components(self):
        self.assertEqual(manage_tools.compare_versions("v1.2", "1.2.0"), 0)
        self.assertLess(manage_tools.compare_versions("1.2.9", "v1.3.0"), 0)
        self.assertGreater(manage_tools.compare_versions("2.0.1-1", "2.0.0"), 0)

    def test_selected_release_asset_requires_sha256(self):
        release = manage_tools.normalize_release(
            {
                "tag_name": "v1.2.3",
                "draft": False,
                "prerelease": False,
                "assets": [
                    {
                        "name": "tool_1.2.3_amd64.deb",
                        "browser_download_url": "https://example.invalid/tool.deb",
                        "digest": None,
                    },
                    {
                        "name": "notes.txt",
                        "browser_download_url": "https://example.invalid/notes.txt",
                        "digest": "sha256:" + "a" * 64,
                    },
                ],
            },
            "tool",
        )

        with self.assertRaisesRegex(manage_tools.InstallerError, "no valid SHA-256"):
            release.require_asset("tool", r"tool_1\.2\.3_amd64\.deb")
        self.assertEqual(release.require_asset("tool", r"notes\.txt").sha256, "a" * 64)


class SelectionTests(unittest.TestCase):
    def test_gpustat_adds_uv_before_itself(self):
        self.assertEqual(
            manage_tools.expand_dependencies(["gpustat"]), ["uv", "gpustat"]
        )

    def test_duplicate_dependencies_are_removed(self):
        self.assertEqual(
            manage_tools.expand_dependencies(["uv", "gpustat", "uv"]),
            ["uv", "gpustat"],
        )

    def test_list_mode_accepts_no_positional_tools(self):
        parser = manage_tools.build_parser()
        args = parser.parse_args(["--list"])

        with mock.patch("builtins.print"):
            self.assertEqual(manage_tools.select_tools(args, parser), [])


class FileSafetyTests(unittest.TestCase):
    def test_safe_extract_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "malicious.tar.gz"
            with tarfile.open(archive_path, "w:gz") as archive:
                member = tarfile.TarInfo("../escape")
                payload = b"bad"
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))

            with self.assertRaisesRegex(
                manage_tools.InstallerError, "escapes destination"
            ):
                manage_tools.safe_extract_tar(archive_path, root / "extract", "example")

    def test_grouped_file_install_rolls_back_both_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work = root / "work"
            home = root / "home"
            work.mkdir()
            source_one = root / "source-one"
            source_two = root / "source-two"
            target_one = home / ".local/bin/tool"
            target_two = home / ".local/share/man/man1/tool.1"
            source_one.write_text("new binary", encoding="utf-8")
            source_two.write_text("new manual", encoding="utf-8")
            target_one.parent.mkdir(parents=True)
            target_two.parent.mkdir(parents=True)
            target_one.write_text("old binary", encoding="utf-8")
            target_two.write_text("old manual", encoding="utf-8")
            installer = manage_tools.Installer(
                manage_tools.PlatformInfo("debian", "12"),
                work,
                False,
                home=home,
            )

            real_replace = os.replace
            failed = False

            def fail_second_install(source, target):
                nonlocal failed
                source_path = Path(source)
                target_path = Path(target)
                if (
                    not failed
                    and target_path == target_two
                    and source_path.name.startswith(".tool.1.new-")
                ):
                    failed = True
                    raise OSError("simulated replacement failure")
                real_replace(source, target)

            with mock.patch("manage_tools.os.replace", side_effect=fail_second_install):
                with self.assertRaisesRegex(manage_tools.InstallerError, "simulated"):
                    installer._atomic_install_files(
                        (
                            (source_one, target_one, 0o755),
                            (source_two, target_two, 0o644),
                        ),
                        "tool",
                    )

            self.assertEqual(target_one.read_text(encoding="utf-8"), "old binary")
            self.assertEqual(target_two.read_text(encoding="utf-8"), "old manual")
            self.assertEqual(list(home.rglob(".*.new-*")), [])
            self.assertEqual(list(home.rglob(".*.old-*")), [])


class FishPolicyTests(unittest.TestCase):
    def make_installer(self, directory, check_only=False):
        root = Path(directory)
        work = root / "work"
        home = root / "home"
        work.mkdir()
        home.mkdir()
        return manage_tools.Installer(
            manage_tools.PlatformInfo("ubuntu", "22.04"),
            work,
            check_only,
            home=home,
        )

    def test_installed_fish_still_stops_for_new_upstream_major(self):
        with tempfile.TemporaryDirectory() as directory:
            installer = self.make_installer(directory)
            with mock.patch.object(
                installer,
                "_package_version_and_conflict",
                return_value="4.3.0-1",
            ), mock.patch.object(
                installer,
                "_latest_release",
                return_value=manage_tools.Release("5.0.0", "5.0.0", ()),
            ), mock.patch.object(installer, "_configure_ppa") as configure:
                with self.assertRaisesRegex(
                    manage_tools.InstallerError, "latest stable fish"
                ):
                    installer._run_fish()

            configure.assert_not_called()

    def test_installed_supported_fish_does_not_touch_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            installer = self.make_installer(directory)
            with mock.patch.object(
                installer,
                "_package_version_and_conflict",
                return_value="4.3.0-1",
            ), mock.patch.object(
                installer,
                "_latest_release",
                return_value=manage_tools.Release("4.4.0", "4.4.0", ()),
            ), mock.patch.object(installer, "_configure_ppa") as configure, mock.patch(
                "builtins.print"
            ):
                installer._run_fish()

            configure.assert_not_called()

    def test_check_only_inspects_repository_without_configuring_it(self):
        with tempfile.TemporaryDirectory() as directory:
            installer = self.make_installer(directory, check_only=True)
            with mock.patch.object(
                installer,
                "_package_version_and_conflict",
                return_value=None,
            ), mock.patch.object(
                installer,
                "_latest_release",
                return_value=manage_tools.Release("4.4.0", "4.4.0", ()),
            ), mock.patch.object(
                installer,
                "_configure_ppa",
                return_value=False,
            ) as configure, mock.patch("builtins.print"):
                installer._run_fish()

            self.assertFalse(configure.call_args.kwargs["configure"])


if __name__ == "__main__":
    unittest.main()
