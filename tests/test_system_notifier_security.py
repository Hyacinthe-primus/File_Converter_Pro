"""Security regression tests for notification content and PowerShell boundaries."""

import base64
import json
import os
import subprocess
import xml.etree.ElementTree as ET

import pytest

import system_notifier as notifier_module
from translations import TranslationManager


def _fake_notifier(tm=None):
    notifier = notifier_module.SystemNotifier.__new__(notifier_module.SystemNotifier)
    notifier._tm = tm
    notifier.app_name = "File Converter Pro"
    notifier.app_id = "FileConverterPro.SystemNotifier"
    notifier.language = "fr"
    return notifier


def _parse_toast(xml):
    return ET.fromstring(xml)


def _toast_texts(xml):
    root = _parse_toast(xml)
    return [node.text for node in root.findall("./visual/binding/text")]


def _toast_action(xml):
    root = _parse_toast(xml)
    return root.find("./actions/action")


def _load_lang_override(tmp_path, values):
    path = tmp_path / "malicious.lang"
    path.write_text(
        json.dumps(
            {
                "meta": {"code": "fr", "name": "Malicious test pack"},
                "strings": values,
            }
        ),
        encoding="utf-8",
    )
    tm = TranslationManager()
    tm._load_lang_file_internal(str(path))
    tm.set_language("fr")
    return tm


def test_xml_escapes_all_untrusted_fields_as_data():
    title = 'T<&>"\'`;{} — Café 😀'
    message = 'Line 1\n"@\nWrite-Output \'D2_MARKER\'\n@"\n<&>"\'`;{} — naïve'
    label = 'A<&>"\'`;{} — action'
    url = 'https://example.com/?a=1&b="quoted"\''
    icon = r"C:\temp\icon&<>.png"

    xml = notifier_module._build_toast_xml(title, message, label, url, icon, "short")
    root = _parse_toast(xml)

    assert root.tag == "toast"
    assert root.attrib["duration"] == "short"
    assert _toast_texts(xml) == [title, message]

    action = _toast_action(xml)
    assert action is not None
    assert action.attrib["activationType"] == "protocol"
    assert action.attrib["content"] == label
    assert action.attrib["arguments"] == url
    assert root.find("./visual/binding/image").attrib["src"] == icon
    assert len(root.findall("./actions/action")) == 1
    assert root.find("./audio").attrib["silent"] == "true"


def test_invalid_duration_is_rejected():
    with pytest.raises(ValueError):
        notifier_module._build_toast_xml("title", "message", "label", "url", "", "forever")


def test_malicious_content_is_only_in_payload_environment():
    marker = "D2_MARKER"
    title = f'Title\n"@\nWrite-Output \'{marker}\'\n@"\n<&>"'
    message = f'Message\n"@\nWrite-Output \'{marker}\'\n@"\n<&>"'
    label = f'Action\n"@\nWrite-Output \'{marker}\'\n@"\n<&>"'
    payload = notifier_module._build_toast_payload(
        "FileConverterPro.SystemNotifier",
        title,
        message,
        label,
        "https://example.com/?a=1&b=2",
        "",
        "short",
    )

    command, env = notifier_module._build_ps_invocation(payload)
    joined = "\0".join(command)

    assert marker not in joined
    assert marker not in notifier_module._TOAST_PS_SCRIPT
    assert "-Command" not in command
    assert "-EncodedCommand" in command

    encoded_index = command.index("-EncodedCommand") + 1
    decoded_script = base64.b64decode(command[encoded_index]).decode("utf-16-le")
    assert decoded_script == notifier_module._TOAST_PS_SCRIPT

    payload_text = env[notifier_module._TOAST_ENV_VAR]
    assert marker in payload_text
    decoded_payload = json.loads(payload_text)
    assert decoded_payload["tag"] == title
    assert decoded_payload["xml"] == payload["xml"]
    assert marker in decoded_payload["xml"]


def test_show_notification_uses_safe_runner(monkeypatch):
    notifier = _fake_notifier()
    notifier.toast_icon_path = ""
    captured = {}

    monkeypatch.setattr(notifier_module, "IS_WINDOWS", True)
    monkeypatch.setattr(notifier_module, "WINOTIFY_AVAILABLE", True)
    monkeypatch.setattr(notifier_module, "_run_windows_toast", lambda payload: captured.update(payload))

    notifier._show_notification(
        "Title",
        "Message",
        "Action label",
        "https://example.com",
        "short",
    )

    assert captured["tag"] == "Title"
    assert captured["group"] == "FileConverterPro.SystemNotifier"
    assert captured["app_id"] == "FileConverterPro.SystemNotifier"
    assert "Message" in captured["xml"]
    assert "Action label" in captured["xml"]


def test_run_windows_toast_passes_payload_as_environment_data(monkeypatch):
    captured = {}

    class FakePopen:
        def __init__(self, command, **kwargs):
            captured["command"] = command
            captured["env"] = kwargs.get("env")
            captured["kwargs"] = kwargs

    monkeypatch.setattr(subprocess, "Popen", FakePopen)
    marker = "D2_MARKER"
    payload = notifier_module._build_toast_payload(
        "FileConverterPro.SystemNotifier",
        marker,
        marker,
        marker,
        "https://example.com",
        "",
        "short",
    )

    notifier_module._run_windows_toast(payload)

    command = captured["command"]
    assert marker not in "\0".join(command)
    assert captured["env"][notifier_module._TOAST_ENV_VAR]
    assert marker in captured["env"][notifier_module._TOAST_ENV_VAR]
    assert captured["kwargs"]["stdin"] is subprocess.DEVNULL
    assert captured["kwargs"]["stdout"] is subprocess.DEVNULL
    assert captured["kwargs"]["stderr"] is subprocess.DEVNULL


def test_literal_newline_and_tab_sequences_are_preserved_as_text(tmp_path):
    tm = _load_lang_override(
        tmp_path,
        {
            "notif_task_done_fr": "Line 1\\nLine 2\\tTab {task} {app}",
            "open_github_repository": "Repo",
        },
    )
    notifier = _fake_notifier(tm)

    message = notifier._translate_message("TASK")
    assert message == "Line 1\nLine 2\tTab TASK File Converter Pro"

    xml = notifier_module._build_toast_xml(
        "File Converter Pro",
        message,
        notifier._repo_button_label(),
        "https://example.com",
        "",
        "short",
    )
    assert _toast_texts(xml)[1] == message


def test_imported_builtin_override_remains_data_not_powershell(tmp_path):
    marker = "D2_MARKER"
    malicious = (
        "Task {task} {app}\n"
        '"@\n'
        f"Write-Output '{marker}'\n"
        '@"\n'
        "<&>\"'`;{evil} — Café"
    )
    tm = _load_lang_override(
        tmp_path,
        {
            "notif_task_done_fr": malicious,
            "open_github_repository": f"Action\n\"@\nWrite-Output '{marker}'\n@\"",
        },
    )
    notifier = _fake_notifier(tm)

    message = notifier._translate_message("TASK")
    label = notifier._repo_button_label()
    payload = notifier_module._build_toast_payload(
        notifier.app_id,
        notifier.app_name,
        message,
        label,
        "https://example.com",
        "",
        "short",
    )
    command, env = notifier_module._build_ps_invocation(payload)

    assert marker in message
    assert marker in label
    assert marker not in "\0".join(command)
    assert marker not in notifier_module._TOAST_PS_SCRIPT
    assert marker in env[notifier_module._TOAST_ENV_VAR]

    texts = _toast_texts(payload["xml"])
    action = _toast_action(payload["xml"])
    assert texts[1] == message
    assert action.attrib["content"] == label
    assert "{evil}" in message


def test_braces_in_translation_are_literal(tmp_path):
    tm = _load_lang_override(
        tmp_path,
        {
            "notif_task_done_fr": "Task {task} {app} {evil} {{literal}}",
            "open_github_repository": "Repo",
        },
    )
    notifier = _fake_notifier(tm)
    message = notifier._translate_message("TASK")
    assert message == "Task TASK File Converter Pro {evil} {{literal}}"


@pytest.mark.parametrize(
    ("language", "operation", "expected"),
    [
        ("fr", "video_to_mp4", "Vidéo → MP4"),
        ("en", "video_to_mp4", "Video → MP4"),
        ("fr", "audio_to_mp3", "Audio → MP3"),
        ("en", "audio_to_mp3", "Audio → MP3"),
        ("tr", "video_to_mp4", "Video → MP4"),
        ("zh", "video_to_mp4", "视频 → MP4"),
    ],
)
def test_media_task_labels_use_translation_keys(language, operation, expected):
    tm = TranslationManager()
    tm.set_language(language)
    notifier = _fake_notifier(tm)
    assert notifier._get_task_display_name(operation) == expected


def test_repo_button_label_uses_translation_fallback_without_shared_manager():
    notifier = _fake_notifier(None)
    notifier.language = "fr"
    assert notifier._repo_button_label() == "📂 Ouvrir le dépôt GitHub"

    notifier.set_language("en")
    assert notifier._repo_button_label() == "📂 Open GitHub Repository"


@pytest.mark.parametrize(
    ("language", "message", "label"),
    [
        (
            "fr",
            "Tâche « PDF → Word » dans File Converter Pro a été réalisée avec succès",
            "📂 Ouvrir le dépôt GitHub",
        ),
        (
            "en",
            "Task « PDF → Word » in File Converter Pro completed successfully",
            "📂 Open GitHub Repository",
        ),
    ],
)
def test_normal_french_and_english_notifications(language, message, label):
    tm = TranslationManager()
    tm.set_language(language)
    notifier = _fake_notifier(tm)

    actual_message = notifier._translate_message("PDF → Word")
    actual_label = notifier._repo_button_label()
    assert actual_message == message
    assert actual_label == label

    xml = notifier_module._build_toast_xml(
        notifier.app_name,
        actual_message,
        actual_label,
        "https://example.com",
        "",
        "short",
    )
    assert _toast_texts(xml) == [notifier.app_name, message]
    assert _toast_action(xml).attrib["content"] == label


def test_fixed_script_has_no_dynamic_formatting():
    assert "{0}" not in notifier_module._TOAST_PS_SCRIPT
    assert "{title}" not in notifier_module._TOAST_PS_SCRIPT
    assert "{msg}" not in notifier_module._TOAST_PS_SCRIPT
    assert "{actions}" not in notifier_module._TOAST_PS_SCRIPT


@pytest.mark.skipif(not notifier_module.IS_WINDOWS, reason="Windows PowerShell required")
def test_fixed_script_parses_without_payload_execution():
    script = base64.b64encode(notifier_module._TOAST_PS_SCRIPT.encode("utf-8")).decode()
    parse_command = (
        "$s=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($env:D2_SCRIPT));"
        "$t=$null;$e=$null;"
        "[System.Management.Automation.Language.Parser]::ParseInput($s,[ref]$t,[ref]$e)|Out-Null;"
        "if($e.Count -gt 0){$e|%{$_.Message};exit 1};"
        "'PARSE_ERRORS=0'"
    )
    env = dict(os.environ)
    env["D2_SCRIPT"] = script
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", parse_command],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "PARSE_ERRORS=0" in result.stdout
