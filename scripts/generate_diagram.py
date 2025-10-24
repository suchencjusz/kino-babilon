from sqlmodel import SQLModel
from sqlalchemy import create_engine
from sqlalchemy_schemadisplay import create_schema_graph

# import your models so SQLModel.metadata knows them
from models import *  # noqa: F401

# create a local sqlite file (or use memory)
engine = create_engine("sqlite:///./kino.db")

# create tables from models
SQLModel.metadata.create_all(engine)

# render the ER diagram
graph = create_schema_graph(
    engine=engine,
    metadata=SQLModel.metadata,
    show_datatypes=False,  # set True to show column types
    show_indexes=False,
    rankdir="LR",
)
graph.write_png("schema.png")
print("Wrote schema.png")