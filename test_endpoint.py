# test_endpoint.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from backend import db, auth
from backend.models import User, Track

app = FastAPI()

@app.get("/test/tracks/{email}")
def test_get_tracks(email: str, session: Session = Depends(db.get_db)):
    print(f"🔹 Testing for: {email}")
    tracks = session.query(Track).filter(Track.personal_code == email).all()
    print(f"✅ Found: {len(tracks)} tracks")
    return [{"track_number": t.track_number, "personal_code": t.personal_code} for t in tracks]
