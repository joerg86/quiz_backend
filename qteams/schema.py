import graphene

import api.schema
from graphql_auth.schema import UserQuery, MeQuery

class Query(MeQuery, api.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass

schema = graphene.Schema(query=Query)