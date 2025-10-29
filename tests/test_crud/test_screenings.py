from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine

from crud.screenings import (
    create_screening,
    delete_screening,
    get_screening,
    get_screenings,
    get_screenings_by_creator,
    update_screening,
)
from crud.user import create_user as create_user_crud
from models import Screening, SelectionMode, User

engine = create_engine("sqlite:///:memory:")


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="test_user")
def user_fixture(session: Session) -> User:
    return create_user_crud(session, discord_id="12345", nickname="TestUser")


@pytest.fixture(name="test_user_2")
def user_fixture_2(session: Session) -> User:
    return create_user_crud(session, discord_id="67890", nickname="TestUser2")


def test_create_screening(session: Session, test_user: User):
    """Test tworzenia nowego seansu."""

    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=2)

    screening = create_screening(
        session=session,
        creator_uid=test_user.uid,
        location="Test Room",
        start_datetime=start_time,
        end_datetime=end_time,
        selection_mode=SelectionMode.OPERATOR_CHOICE,
        description="Testowy seans.",
        mid=1,
    )

    assert screening.sid is not None
    assert screening.creator_uid == test_user.uid
    assert screening.location == "Test Room"
    assert screening.selection_mode == SelectionMode.OPERATOR_CHOICE
    assert screening.mid == 1

    db_screening = session.get(Screening, screening.sid)
    assert db_screening is not None
    assert db_screening.description == "Testowy seans."


def test_get_screening(session: Session, test_user: User):
    """Test pobierania seansu po jego ID."""
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=2)
    new_screening = create_screening(
        session, test_user.uid, "Room 1", start_time, end_time, SelectionMode.OPEN_VOTE
    )

    found_screening = get_screening(session, new_screening.sid)
    assert found_screening is not None
    assert found_screening.sid == new_screening.sid
    assert found_screening.location == "Room 1"

    not_found_screening = get_screening(session, 999)
    assert not_found_screening is None


def test_get_screenings(session: Session, test_user: User):
    """Test pobierania listy seansów z paginacją."""

    start_time = datetime.now(timezone.utc)
    for i in range(5):
        create_screening(
            session,
            test_user.uid,
            f"Room {i}",
            start_time + timedelta(days=i),
            start_time + timedelta(days=i, hours=2),
            SelectionMode.CURATED_VOTE,
        )

    # Pobierz wszystkie seanse
    all_screenings = get_screenings(session)
    assert len(all_screenings) == 5

    # Test limitu
    limited_screenings = get_screenings(session, limit=2)
    assert len(limited_screenings) == 2

    # Test pomijania
    skipped_screenings = get_screenings(session, skip=3)
    assert len(skipped_screenings) == 2
    assert skipped_screenings[0].location == "Room 3"

    # Test paginacji (skip + limit)
    paginated_screenings = get_screenings(session, skip=1, limit=2)
    assert len(paginated_screenings) == 2
    assert paginated_screenings[0].location == "Room 1"


def test_get_screenings_by_creator(
    session: Session, test_user: User, test_user_2: User
):
    """Test pobierania seansów utworzonych przez konkretnego użytkownika."""

    start_time = datetime.now(timezone.utc)

    create_screening(
        session,
        test_user.uid,
        "U1 Room 1",
        start_time,
        start_time + timedelta(hours=2),
        SelectionMode.OPEN_VOTE,
    )
    create_screening(
        session,
        test_user.uid,
        "U1 Room 2",
        start_time,
        start_time + timedelta(hours=2),
        SelectionMode.OPEN_VOTE,
    )
    create_screening(
        session,
        test_user_2.uid,
        "U2 Room 1",
        start_time,
        start_time + timedelta(hours=2),
        SelectionMode.OPEN_VOTE,
    )

    user1_screenings = get_screenings_by_creator(session, test_user.uid)
    assert len(user1_screenings) == 2
    assert all(s.creator_uid == test_user.uid for s in user1_screenings)

    user2_screenings = get_screenings_by_creator(session, test_user_2.uid)
    assert len(user2_screenings) == 1
    assert user2_screenings[0].creator_uid == test_user_2.uid


def test_update_screening(session: Session, test_user: User):
    """Test aktualizacji istniejącego seansu."""

    start_time = datetime.now(timezone.utc)
    screening = create_screening(
        session,
        test_user.uid,
        "Old Location",
        start_time,
        start_time + timedelta(hours=2),
        SelectionMode.OPERATOR_CHOICE,
    )

    update_data = {
        "location": "New Location",
        "description": "Zaktualizowany opis.",
        "selection_mode": SelectionMode.OPEN_VOTE,
    }
    updated_screening = update_screening(session, screening, **update_data)

    assert updated_screening.location == "New Location"
    assert updated_screening.description == "Zaktualizowany opis."
    assert updated_screening.selection_mode == SelectionMode.OPEN_VOTE
    assert updated_screening.sid == screening.sid

    db_screening = get_screening(session, screening.sid)
    assert db_screening.location == "New Location"


def test_delete_screening(session: Session, test_user: User):
    """Test usuwania seansu."""

    screening = create_screening(
        session,
        test_user.uid,
        "Do usunięcia",
        datetime.now(timezone.utc),
        datetime.now(timezone.utc) + timedelta(hours=2),
        SelectionMode.OPERATOR_CHOICE,
    )
    sid = screening.sid

    deleted_screening = delete_screening(session, sid)
    assert deleted_screening is not None
    assert deleted_screening.sid == sid

    assert get_screening(session, sid) is None

    non_existent_deleted = delete_screening(session, 999)
    assert non_existent_deleted is None
