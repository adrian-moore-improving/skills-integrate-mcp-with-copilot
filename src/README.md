# Mergington High School Activities API

A simple FastAPI application that allows students to view activities and
teachers to manage student enrollments.

## Features

- View all available extracurricular activities
- Teachers can sign up and unregister students after logging in
- Students can view activities and registered participants

## Teacher Accounts

Teacher usernames and salted PBKDF2 password hashes are stored in
`src/teachers.json`; plaintext passwords are not stored. Provision an account
from the `src` directory with:

```sh
python create_teacher.py <username>
```

The utility prompts for the password twice. Restart the application after
changing teacher accounts. Teacher login sessions are held in memory, expire
after eight hours, and are cleared when the server restarts. The browser keeps
the bearer token only in memory, so a teacher must log in again after reloading
the page.

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Log in with a provisioned teacher username and password             |
| POST   | `/auth/logout`                                                     | Revoke the current teacher session                                  |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only student enrollment                                    |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only student unregistration                               |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
