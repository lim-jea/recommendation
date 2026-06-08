import json

from fastapi import FastAPI
import uvicorn
from model import CourseRecord

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/courses")
async def read_courses():
    with open("course_record.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.post("/courses")
async def create_course(new_course: CourseRecord):
    with open("course_record.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append(new_course.model_dump())

    with open("course_record.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return new_course

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
