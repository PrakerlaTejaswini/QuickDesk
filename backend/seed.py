from app.database import Base, engine, SessionLocal
from app.models import User
from app.auth import hash_password


def seed_database():

    # Create all database tables
    Base.metadata.create_all(bind=engine)

    # Open database connection
    db = SessionLocal()

    try:

        # ------------------------------------------------
        # CREATE DEMO AGENT
        # ------------------------------------------------

        agent = db.query(User).filter(
            User.email == "agent@quickdesk.local"
        ).first()

        if not agent:

            agent = User(
                name="Support Agent",
                email="agent@quickdesk.local",
                password_hash=hash_password(
                    "agent123"
                ),
                role="agent"
            )

            db.add(agent)

            print("Agent user created.")

        else:

            print("Agent user already exists.")


        # ------------------------------------------------
        # CREATE DEMO EMPLOYEE
        # ------------------------------------------------

        employee = db.query(User).filter(
            User.email == "employee@quickdesk.local"
        ).first()

        if not employee:

            employee = User(
                name="Demo Employee",
                email="employee@quickdesk.local",
                password_hash=hash_password(
                    "employee123"
                ),
                role="employee"
            )

            db.add(employee)

            print("Employee user created.")

        else:

            print("Employee user already exists.")


        # Save changes
        db.commit()

        print()
        print("=" * 50)
        print("QuickDesk database seeded successfully")
        print("=" * 50)

        print()
        print("AGENT LOGIN")
        print("Email    : agent@quickdesk.local")
        print("Password : agent123")

        print()
        print("EMPLOYEE LOGIN")
        print("Email    : employee@quickdesk.local")
        print("Password : employee123")

        print()
        print("Database is ready.")


    except Exception as e:

        db.rollback()

        print("Error while seeding database:")
        print(e)

        raise

    finally:

        db.close()


if __name__ == "__main__":
    seed_database()