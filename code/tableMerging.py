from __future__ import print_function
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
import pandas as pd

engine = create_engine('sqlite://')

Base = declarative_base()

class A(Base):
    __tablename__ = 'a'

    id = Column(Integer, primary_key=True)
    name = Column(String(10))

    def __repr__(self):
        return 'id:%s, name:%s' % (self.id, self.name)

class B(Base):
    __tablename__ = 'b'

    id = Column(Integer, primary_key=True)
    name = Column(String(10))
    age = Column(String(3)) # just to test as_type

    def __repr__(self):
        return 'id:%s, name:%s, age:%s' % (self.id, self.name, self.age)


Session = sessionmaker(engine)
session = Session()

Base.metadata.create_all(engine, checkfirst=True)

session.add_all([A(name='lola'), A(name='Josiah')])
session.add_all([B(name='Joe', age='26')])


session.commit()

print("A")
print(session.query(A).all())

print("B")
print(session.query(B).all())

# session_1 = Session()
session.merge(A(id=1,name='Kjah'))
session.commit()

print("Merged A")
print(session.query(A).all())

df = pd.DataFrame({'id':[1,2,3], 'name':['Jah', 'jaK', 'Lka'], 'age':[29,34,21]})

print('df')
print(df.head())

print('inserting into c')
try:
    df.to_sql(name='c', con=engine, if_exists='append', index=False,
              dtype={'id':Integer, 'name':String, 'age':String})
    print('worked')
    print(pd.read_sql("select * from c", con=engine))
except:
    print('failed')


print('inserting into b')


try:
    df.to_sql(name='b', con=engine, if_exists='append', index=False,
              dtype={'id': Integer, 'name': String, 'age': String})
    print('worked')
    print(pd.read_sql("select * from b", con=engine))
except IntegrityError as e:
    print('failed: %s' % e.args[0])
    print('trying with id not in B')

try:
    df.loc[1:,].to_sql(name='b', con=engine, if_exists='append', index=False,
                       dtype={'id': Integer, 'name': String, 'age': String})
    print('worked')
    print(pd.read_sql("select * from b", con=engine))
    print('conclusion: the type conversion works. Need more tests')
    print('conclusion: to_sql does not take care of IntegrityError')
except:
    print('something happened. check')

#3 we could use a query to get ids we need to change/drop
# we can use c as the staging datatable.
ids = pd.read_sql("select A.id from b as A, c as B where A.id=B.id", con=engine)
# then we can use bulk update on the rows we want to keep and those we want to drop.
# might even be able to use index=True in to_sql when creating staging table.
# that way I can use that index to split the daaframe. Then I will know what to do with each
# subset
print(ids)