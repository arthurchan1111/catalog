import sys
from sqlalchemy import
Column, ForeignKey, Integer, String, Enum

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relation
from sql alchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable= False)

    @property
    def serialize(self):
        return{
            'name' :self.name,
            'id'   : self.id,
    }

class Recipe(Base):
    __tablename__='recipe'

    name= Column(String(80), nullable=False)
    id= Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(250))
    prep_time= Column(DateTime, )
    cook_time= Column(DateTime, )
    category_name = Column(Integer, ForeignKey('categories.id'))
    user_id= Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    category=relationship(Category)

    @property
    def serialize(self):
        return{
            'name' :self.name,
            'id'   : self.id,
            'description': self.description,
            'prep_time': self.prep_time
            'cook_time': self.cook_time,
            'category': self.category_name

    }

class Ingredients(Base):
    __tablename__='ingredient'

    ingredient_name= Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True, autoincrement=True)

        @property
        def serialize(self):
            return{
                'name' :self.ingredient_name,
                'id'   : self.id,


        }

class Measurements(Base):
    __tablename__='measurement'

    id = Column(Integer, primary_key=True, autoincrement=True)
    measurement_name= Column(String(80), nullable=False)

            @property
            def serialize(self):
                return{
                    'name' :self.measurement_name,
                    'id'   : self.id,


            }

class IngredientList(Base):
    __tablename__= 'ingredientlist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    quantity= Column(Float, nullable=False)
    ingredient_id= Column(Integer, ForeignKey('ingredient.id'))
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    ingredient = relationship(Ingredients)
    measurement = relationship(Measurements)
    recipe= relationship(Recipe)

class Steps(Base):
    __tablename__='steps'

    step_id= Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    step_number= Column(Integer, nullable= False)
    step_description= Column(String(500), nullable=False)
    recipe= relationship(Recipe)

class Categories(Base):
    __tablename__-'categories'

    id= Column(Integer, primary_key=True, autoincrement=True)
    name= Column(String(80))
        @property
        def serialize(self):
            return{
                'name' :self.name,
                'id'   : self.id,


        }

engine = create_engine('sqlite:///catalog.db')

base.metadata.create_all(engine)
