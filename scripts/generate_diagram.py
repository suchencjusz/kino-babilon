from sqlmodel import SQLModel
from sqlalchemy import create_engine
from sqlalchemy_schemadisplay import create_schema_graph

# import your models so SQLModel.metadata knows them
from models import *  # noqa: F401

engine = create_engine("sqlite:///:memory:")

# create tables from models
SQLModel.metadata.create_all(engine)

# render the ER diagram
graph = create_schema_graph(
    engine=engine,
    metadata=SQLModel.metadata,
    show_datatypes=True,
    show_indexes=True,
    rankdir="LR",
)
graph.write_png("schema.png")
print("Wrote schema.png")