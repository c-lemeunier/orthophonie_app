from auth import crypto


def test_password_hash_and_verify():
    password_hash = crypto.hash_password("un-mot-de-passe-solide")
    assert crypto.verify_password("un-mot-de-passe-solide", password_hash) is True
    assert crypto.verify_password("mauvais-mot-de-passe", password_hash) is False


def test_dek_wrap_unwrap_roundtrip():
    dek = crypto.generate_dek()
    wrapped = crypto.wrap_dek(dek, "mon-mot-de-passe")

    unwrapped = crypto.unwrap_dek(wrapped, "mon-mot-de-passe")
    assert unwrapped == dek


def test_dek_unwrap_rejects_wrong_secret():
    dek = crypto.generate_dek()
    wrapped = crypto.wrap_dek(dek, "mon-mot-de-passe")

    assert crypto.unwrap_dek(wrapped, "mauvais-mot-de-passe") is None


def test_recovery_code_can_also_unlock_dek():
    dek = crypto.generate_dek()
    recovery_code = crypto.generate_recovery_code()
    wrapped = crypto.wrap_dek(dek, crypto.normalize_recovery_code(recovery_code))

    unwrapped = crypto.unwrap_dek(wrapped, crypto.normalize_recovery_code(recovery_code))
    assert unwrapped == dek


def test_recovery_code_format():
    code = crypto.generate_recovery_code()
    groups = code.split("-")
    assert len(groups) == crypto.RECOVERY_CODE_GROUPS
    assert all(len(g) == crypto.RECOVERY_CODE_GROUP_LEN for g in groups)
