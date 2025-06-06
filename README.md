# Ticket Booking System

A modern ticket booking system built with Flask, SQLAlchemy, and Celery.

## Features

- User authentication and authorization
- Event browsing and searching
- Ticket booking and management
- Payment processing
- Email notifications
- Admin dashboard
- Background task processing

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ticket_booking
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=postgresql://user:password@localhost/ticket_booking
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379
STRIPE_SECRET_KEY=your-stripe-secret-key
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

7. Start Celery worker (in a separate terminal):
```bash
celery -A celery_worker.celery worker --loglevel=info
```

## Testing

Run tests using pytest:
```bash
pytest
```

## Project Structure

- `app/`: Main application package
  - `models/`: Database models
  - `routes/`: Route handlers
  - `services/`: Business logic
  - `tasks/`: Celery tasks
  - `templates/`: HTML templates
  - `static/`: Static files
  - `utils/`: Utility functions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 