from app.core.database import SessionLocal
from app.models.centre import Centre
from app.models.test import Test
from app.models.centre_test import CentreTest

db = SessionLocal()

centre1 = Centre(name="Apollo Diagnostics", location="Delhi")
centre2 = Centre(name="MedLife Labs", location="Ghaziabad")

test1 = Test(name="Complete Blood Count")
test2 = Test(name="Thyroid Profile")
test3 = Test(name="Lipid Profile")

db.add_all([centre1, centre2, test1, test2, test3])
db.commit()

db.add_all([
    CentreTest(centre_id=centre1.id, test_id=test1.id, price=500),
    CentreTest(centre_id=centre1.id, test_id=test2.id, price=800),
    CentreTest(centre_id=centre2.id, test_id=test1.id, price=450),
    CentreTest(centre_id=centre2.id, test_id=test3.id, price=650),
])
db.commit()

print("seeded")
db.close()