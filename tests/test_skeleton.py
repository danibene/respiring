from pytest import CaptureFixture

from respiring.skeleton import main

__author__ = "danibene"
__copyright__ = "danibene"
__license__ = "MIT"


def test_main(capsys: CaptureFixture) -> None:
    """CLI Tests"""
    # capsys is a pytest fixture that allows asserts against stdout/stderr
    # https://docs.pytest.org/en/stable/capture.html
    main(["--pattern", "6, 0, 6"])
    captured = capsys.readouterr()
    assert "Building video" in captured.out
