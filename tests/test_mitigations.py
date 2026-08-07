from mitigations.sandwich import sandwich
from mitigations.delimiting import delimit_user_prompt as delimit


def test_sandwich_leaves_system_prompt_unchanged():
    system_prompt = "You are a helpful assistant."
    new_system_prompt, _ = sandwich(system_prompt, "some user text")
    assert new_system_prompt == system_prompt


def test_sandwich_preserves_original_user_prompt_content():
    user_prompt = "Please summarize this email."
    _, new_user_prompt = sandwich("system", user_prompt)
    assert user_prompt in new_user_prompt


def test_sandwich_appends_reminder_after_user_content():
    user_prompt = "Please summarize this email."
    _, new_user_prompt = sandwich("system", user_prompt)
    assert new_user_prompt.index(user_prompt) < new_user_prompt.index("Reminder")


def test_delimit_preserves_original_system_prompt_content():
    system_prompt = "You are a helpful assistant."
    new_system_prompt, _ = delimit(system_prompt, "some user text")
    assert system_prompt in new_system_prompt


def test_delimit_adds_tag_meaning_instruction_to_system_prompt():
    new_system_prompt, _ = delimit("system", "some user text")
    assert "<user_input>" in new_system_prompt
    assert "data" in new_system_prompt.lower()


def test_delimit_wraps_user_prompt_in_tags():
    user_prompt = "Please summarize this email."
    _, new_user_prompt = delimit("system", user_prompt)
    assert new_user_prompt.startswith("<user_input>")
    assert new_user_prompt.endswith("</user_input>")


def test_delimit_preserves_original_user_prompt_content():
    user_prompt = "Please summarize this email."
    _, new_user_prompt = delimit("system", user_prompt)
    assert user_prompt in new_user_prompt


def test_mitigations_return_tuple_of_two_strings():
    result = sandwich("system", "user")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(isinstance(part, str) for part in result)

    result = delimit("system", "user")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert all(isinstance(part, str) for part in result)
