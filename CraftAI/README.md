# CraftAI

CraftAI is a simple web application focused on user authentication and prepared for future AI integration.
Right now, the project handles user registration and login, with a clean structure to grow into something bigger.

---

## What it does

* Create user accounts
* Login with authentication (JWT)
* Protect routes on the backend

---

## Tech Stack

**Backend**

* Python
* FastAPI
* SQLAlchemy

**Frontend**

* React
* Vite

**Database**

* PostgreSQL

---

## Project Structure

```
backend/
  app/
    routes/
    models/
    schemas/
    services/
    main.py

frontend/
  src/
```

---

## Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Environment variables

Create a `.env` file in the backend:

```
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```

---

## Notes

This project is still in progress.
The idea is to expand it later with AI features like product suggestions and image generation.

---

## Author

Eduarda Fernandes Pires
Igor Samuel Candido de Souza
