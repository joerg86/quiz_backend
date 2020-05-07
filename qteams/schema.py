import graphene

import api.schema
from graphql_auth.schema import UserQuery, MeQuery

class Query(api.schema.Query, MeQuery, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass

class Subscription(api.schema.Subscription):
    pass

schema = graphene.Schema(
    query=Query,
    subscription=Subscription,    
)