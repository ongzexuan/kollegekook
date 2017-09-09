#!/usr/bin/env python

import json

from bottle import get, run, request, response, static_file
from py2neo import Graph

graph = Graph("http://neo4j:password@localhost:7474/db/data")

@get("/")
def get_index():
    return static_file("index.html", root="static")

@get("/<filename:re:.*\.css>")
def stylesheets(filename):
    return static_file(filename, root="static")

@get("/<filename:re:.*\.jpg>")
def stylesheets(filename):
    return static_file(filename, root="static")

@get("/<filename:re:.*\.html>")
def stylesheets(filename):
    return static_file(filename, root="static")


@get("/graph")
def get_graph():
    results = graph.cypher.execute(
        "MATCH(r:Recipe) < -[: Ingredient_in]-(i: Ingredient) "
        "RETURN r.title as recipe, collect(i.name) as ingredients"
    )
    nodes = []
    rels = []
    i = 0
    for recipe, ingredients in results:
        nodes.append({"recipe": recipe, "label": "dish"})
        target = i
        i += 1
        for name in ingredients:
            ingredient = {"ingredient": name, "label": "ingredient"}
            try:
                source = nodes.index(ingredient)
            except ValueError:
                nodes.append(ingredient)
                source = i
                i += 1
            rels.append({"source": source, "target": target})
    return {"nodes": nodes, "links": rels}


@get("/search")
def get_search():
    try:
        q = request.query["q"]
    except KeyError:
        return []
    else:
        results = graph.cypher.execute(
            "MATCH (dish: Dish) "
            "WHERE movie.title =~ {title} "
            "RETURN movie", {"title": "(?i).*" + q + ".*"}
        )
        response.content_type = "application/json"
        return json.dumps([{"movie": row.movie.properties} for row in results])


@get("/recipe/<title>")
def get_recipe(title):
    results = graph.cypher.execute(
        "MATCH (recipe:Recipe {title:{title}}) "
        "RETURN movie.title as title,"
        "collect([person.name, head(split(lower(type(r)),'_')), r.roles]) as cast "
        "LIMIT 1", {"title": title})
    row = results[0]
    return {"title": row.title,
            "cast": [dict(zip(("name", "job", "role"), member)) for member in row.cast]}


@get("/search_recipe")
def search_recipe():
    try:
        q = request.query["q"]
        # q is comma-separated string of ingredients
    except KeyError:
        return []
    else:
        ingredient_list = q.split(',')

        ingredient_set = "['"
        for ingredient in ingredient_list:
            ingredient_set += ingredient + "','"
        ingredient_set -= ",'"
        ingredient_set += "]"

        # ingredient_set is a string of the form ['Oil','Water'] e.g.

        results = graph.cypher.execute(
            "MATCH (n:Recipe)<-[:Ingredient_in]-(i:Ingredient)"
            "WHERE i.name IN {ingredient_set: ingredient_set}"
            "RETURN (n)<-[:Ingredient_in]-(:Ingredient)",
            {"ingredient_set": ingredient_set}
        )
        # Note: passing a dictionary as second parameter to graph.cypher.execute
        # has not been tested; the first 3 lines have been tested in Neo4J

        return json.dumps([{"recipe": row.n.properties} for row in results])


@get("/search_ingredients")
def search_ingredients():
    try:
    except KeyError:
        return []
    results = graph.cypher.execute(
        #"MATCH (n) RETURN n;"
        "MATCH ((i:Ingredient)-[Ingredient_in]->(r:Recipe {name: "+q+"})) RETURN collect(i.name) as ingredients;"
    )
    response.content_type = "application/json"
    return json.dumps([{"recipe": row.n.properties} for row in results])


if __name__ == "__main__":
    run(port=8080)
