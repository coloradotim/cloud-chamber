from pytest import CaptureFixture

from cloud_chamber.cli import ENGINE_NOTE, main


def test_doctor_identifies_cm1_and_cloud_chamber(capsys: CaptureFixture[str]) -> None:
    exit_code = main(["doctor"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "CM1 is the high-fidelity simulation engine" in captured.out
    assert "Cloud Chamber is the local experiment builder" in captured.out
    assert ENGINE_NOTE in captured.out
