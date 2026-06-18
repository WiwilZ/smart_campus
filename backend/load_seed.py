import json
import os
from sqlmodel import Session, SQLModel, create_engine
from app.models.point import Point
from app.models.task import Task
from app.models.alert import Alert
from app.models.command import Command
from app.models.inspector import Inspector
from app.models.report import RealtimeReport
from app.core.database import engine

def load_seed():
    # create tables
    SQLModel.metadata.create_all(engine)
    
    with open("seed_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    with Session(engine) as session:
        # Check if already seeded
        if session.query(Point).first() is not None:
            print("Database already contains data.")
            return

        print("Seeding points...")
        for p in data.get("points", []):
            point = Point(
                id=p.get("id"),
                name=p.get("name"),
                coordinates=p.get("coordinates", "116.404, 39.915"),
                description=p.get("description"),
                creatorName=p.get("creatorName", "admin"),
                createTime=p.get("createTime", "2026-06-18 10:00:00"),
                modifierName=p.get("modifierName", "admin"),
                modifyTime=p.get("modifyTime", "2026-06-18 10:00:00"),
                status=p.get("status", "normal"),
                riskLevel=p.get("riskLevel", "low")
            )
            session.add(point)
            
        print("Seeding tasks...")
        for t in data.get("tasks", []):
            task = Task(
                id=t.get("id"),
                name=t.get("name") or t.get("title", "未命名任务"),
                point=t.get("point") or t.get("pointName"),
                robot=t.get("robot", "Robot-01"),
                status=t.get("status", "pending"),
                startTime=t.get("startTime") or t.get("plannedStart"),
                endTime=t.get("endTime"),
                description=t.get("description"),
                creatorName=t.get("creatorName", "admin"),
                createTime=t.get("createTime", "2026-06-18 10:00:00"),
                modifierName=t.get("modifierName", "admin"),
                modifyTime=t.get("modifyTime", "2026-06-18 10:00:00")
            )
            session.add(task)

        print("Seeding alerts...")
        for a in data.get("alerts", []):
            alert = Alert(
                id=a.get("id"),
                time=a.get("time") or a.get("createdAt"),
                location=a.get("location") or "校园",
                image=a.get("image", ""),
                description=a.get("description") or a.get("content", ""),
                level=a.get("level", "medium"),
                title=a.get("title", "")
            )
            session.add(alert)
            
        print("Seeding commands...")
        for c in data.get("commands", []):
            command = Command(
                id=c.get("id"),
                command=c.get("command"),
                target=c.get("target"),
                operator=c.get("operator"),
                status=c.get("status"),
                createdAt=c.get("createdAt"),
                result=c.get("result")
            )
            session.add(command)
            
        print("Seeding inspectors...")
        for i in data.get("inspectors", []):
            inspector = Inspector(
                id=i.get("id"),
                name=i.get("name"),
                phone=i.get("phone", ""),
                shift=i.get("shift", ""),
                status=i.get("status", ""),
                title=i.get("title", "")
            )
            session.add(inspector)
            
        print("Seeding realtime rows...")
        for r in data.get("realtimeRows", []):
            report = RealtimeReport(
                id=r.get("id"),
                pointName=r.get("pointName"),
                metric=r.get("metric"),
                value=r.get("value"),
                time=r.get("time"),
                status=r.get("status", "normal")
            )
            session.add(report)

        session.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    load_seed()
