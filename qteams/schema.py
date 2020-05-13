import graphene

import api.schema

import graphql_jwt

class AuthMutation(graphene.ObjectType):
    #token_auth = relay.ObtainJSONWebToken.Field()
    token_auth = graphql_jwt.relay.ObtainJSONWebToken.Field()


class Query(api.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass

class Subscription(api.schema.Subscription):
    pass

class Mutation(AuthMutation, api.schema.Mutation):
    pass

schema = graphene.Schema(
    query=Query,
    subscription=Subscription,   
    mutation=Mutation, 
)