import sys
from sqlalchemy import Column, ForeignKey, Float, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable=False)
    email = Column(String(250), nullable=False)


class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), nullable=False)

    @property
    def serialize(self):
        return{
            'name': self.name
        }


class Recipe(Base):
    __tablename__ = 'recipe'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(250))
    prep_time = Column(Integer, nullable=False)
    cook_time = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    category = relationship(Categories)

    @property
    def serialize(self):
        return{
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            }


class IngredientList(Base):
    __tablename__ = 'ingredientlist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingredient = Column(String(80), nullable=False)
    ingredient_number = Column(Integer, nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    recipe = relationship(Recipe)

    @property
    def serialize(self):
        return{

            'id': self.id,
            'ingredient': self.ingredient

            }


class Steps(Base):
    __tablename__ = 'steps'

    step_id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    step_number = Column(Integer, nullable=False)
    step_description = Column(String(1000), nullable=False)
    recipe = relationship(Recipe)

    @property
    def serialize(self):
        return{
            'id': self.step_id,
            'step_number': self.step_number,
            'step_description': self.step_description
        }

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
