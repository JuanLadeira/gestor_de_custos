import pytest

from app.authz import catalog


@pytest.mark.authz
def test_all_codes_unique_and_nonempty():
    codes = catalog.all_codes()
    assert len(codes) == len(set(codes))
    assert "custo:create" in codes
    assert "rateio:pay" in codes


@pytest.mark.authz
def test_codes_for_grupos_filters():
    custo_codes = catalog.codes_for_grupos("custo")
    assert "custo:create" in custo_codes
    assert "rateio:pay" not in custo_codes


@pytest.mark.authz
def test_read_codes_only_reads():
    assert all(c.endswith(":read") for c in catalog.read_codes())
    assert "custo:read" in catalog.read_codes()


@pytest.mark.authz
def test_default_roles_reference_real_codes():
    valid = set(catalog.all_codes())
    for role, codes in catalog.DEFAULT_ROLES.items():
        for c in codes:
            assert c in valid, f"role {role} references unknown code {c}"


@pytest.mark.authz
def test_default_profiles_reference_real_roles():
    role_names = set(catalog.DEFAULT_ROLES)
    assert "Dono" in catalog.DEFAULT_PROFILES
    assert catalog.DEFAULT_PROFILES["Dono"]["is_protected"] is True
    for profile, spec in catalog.DEFAULT_PROFILES.items():
        for r in spec["roles"]:
            assert r in role_names, f"profile {profile} references unknown role {r}"


@pytest.mark.authz
def test_dono_profile_covers_all_permissions():
    # The Dono profile's roles must union to the full catalog.
    dono_roles = catalog.DEFAULT_PROFILES["Dono"]["roles"]
    covered = set()
    for r in dono_roles:
        covered.update(catalog.DEFAULT_ROLES[r])
    assert covered == set(catalog.all_codes())
