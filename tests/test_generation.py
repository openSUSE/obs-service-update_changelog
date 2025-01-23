import pytz
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, mock_open

from updatechangelog import common


def test_nothing_new():
    os_mock = Mock()
    os_mock.getcwd.return_value = ""
    Repo_mock = MagicMock()
    open_mock = mock_open()
    with patch.multiple(common, os=os_mock, Repo=Repo_mock, open=open_mock):
        common.main()
    open_mock().write.assert_called_once()


def test_rendering():
    template = common.get_template()
    messages = ["First entry", "Second entry"]
    name = "Fake Name"
    email = "fake@example.com"
    added = ["first_added.patch", "second_added.patch"]
    modified = ["first_modified.patch", "second_modified.patch"]
    deleted = ["first_deleted.patch", "second_deleted.patch"]
    current_dt = datetime.now().replace(tzinfo=pytz.utc)

    changelog_entry = template.render(
        messages=messages,
        added=added,
        modified=modified,
        deleted=deleted,
    ).strip()
    expected = ""
    with open("tests/expected.output", "r") as f:
        expected = f.read().strip()
    assert changelog_entry == expected


def test_new_commit():
    os_mock = Mock()
    os_mock.getcwd.return_value = ""
    Repo_mock = MagicMock()
    open_mock = mock_open()

    commit1_mock = MagicMock()
    commit1_mock.configure_mock(hexsha="abcdef12345")
    commit1_mock.tree.side_effect = [
        {"salt": [Mock(path="existing.patch")]},
    ]

    commit2_mock = MagicMock()
    commit2_mock.configure_mock(hexsha="abcdef12345")
    commit2_mock.tree.side_effect = [
        {"salt": [Mock(path="current.patch")]},
    ]

    Repo_mock.return_value.commit.side_effects = [commit1_mock, commit2_mock]

    with patch.multiple(common, os=os_mock, Repo=Repo_mock, open=open_mock):
        common.main()
    open_mock().write.assert_called_once()
