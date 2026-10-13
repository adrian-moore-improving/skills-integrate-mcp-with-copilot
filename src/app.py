"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import time

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

TEACHERS_FILE = current_dir / "teachers.json"
PASSWORD_HASH_ITERATIONS = 600_000
SESSION_DURATION_SECONDS = 8 * 60 * 60
DUMMY_SALT = b"mergington-teacher-auth"
bearer_scheme = HTTPBearer(auto_error=False)
teacher_sessions: dict[str, tuple[str, float]] = {}


def load_teachers() -> dict[str, dict[str, str]]:
    """Load provisioned teacher password hashes from the credentials file."""
    with TEACHERS_FILE.open(encoding="utf-8") as credentials_file:
        credentials = json.load(credentials_file)

    if not isinstance(credentials, dict):
        raise ValueError(f"{TEACHERS_FILE} must contain a JSON object")
    teachers = credentials.get("teachers")
    if not isinstance(teachers, dict):
        raise ValueError(f"{TEACHERS_FILE} must contain a 'teachers' object")

    for username, record in teachers.items():
        if (
            not isinstance(username, str)
            or not username.strip()
            or not isinstance(record, dict)
            or not isinstance(record.get("salt"), str)
            or not isinstance(record.get("password_hash"), str)
        ):
            raise ValueError(f"Invalid teacher credential record in {TEACHERS_FILE}")
        try:
            salt = bytes.fromhex(record["salt"])
            password_hash = bytes.fromhex(record["password_hash"])
        except ValueError as error:
            raise ValueError(
                f"Invalid teacher credential encoding in {TEACHERS_FILE}"
            ) from error
        if len(salt) != 16 or len(password_hash) != hashlib.sha256().digest_size:
            raise ValueError(f"Invalid teacher password hash in {TEACHERS_FILE}")

    return teachers


teachers = load_teachers()


def hash_password(password: str, salt: bytes | None = None) -> dict[str, str]:
    """Create a salted PBKDF2 password record suitable for teachers.json."""
    salt = salt or secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return {"salt": salt.hex(), "password_hash": password_hash.hex()}


def verify_teacher_password(username: str, password: str) -> bool:
    """Verify a teacher password without revealing whether the username exists."""
    record = teachers.get(username)
    salt = bytes.fromhex(record["salt"]) if record else DUMMY_SALT
    expected_hash = record["password_hash"] if record else "0" * 64
    actual_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    ).hex()
    return hmac.compare_digest(actual_hash, expected_hash) and record is not None


def require_teacher(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Require a valid, unexpired teacher bearer token."""
    if credentials is not None:
        session = teacher_sessions.get(credentials.credentials)
        if session is not None:
            username, expires_at = session
            if expires_at > time.time():
                return username
            teacher_sessions.pop(credentials.credentials, None)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Teacher login required",
        headers={"WWW-Authenticate": "Bearer"},
    )


class TeacherLogin(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
def login_teacher(login: TeacherLogin):
    """Authenticate a teacher and issue a short-lived bearer token."""
    if not verify_teacher_password(login.username, login.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    now = time.time()
    for token, (_, expires_at) in list(teacher_sessions.items()):
        if expires_at <= now:
            teacher_sessions.pop(token, None)

    access_token = secrets.token_urlsafe(32)
    teacher_sessions[access_token] = (
        login.username,
        now + SESSION_DURATION_SECONDS,
    )
    return {"access_token": access_token, "username": login.username}


@app.post("/auth/logout")
def logout_teacher(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """Revoke the current teacher bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Teacher login required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    require_teacher(credentials)
    teacher_sessions.pop(credentials.credentials, None)
    return {"message": "Logged out"}


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str,
                         _: str = Depends(require_teacher)):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str,
                             _: str = Depends(require_teacher)):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
