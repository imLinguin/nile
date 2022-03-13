import requests
import logging
import locale
import os
import nile.constants as constants


class GraphQLHandler:
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = requests.Session()
        print(os.environ)
        lang, encoding = locale.getdefaultlocale()
        lang = lang.replace("_", "-")
        self.session.headers.update(
            {
                "User-Agent": "GraphQL.Client/3.2.2.0",
                "client-id": "AmazonGamesApp",
                "prime-gaming-language": lang,
                "Content-Type": "application/json; charset=utf-8",
            }
        )

    def make_graphql_request(self, data):
        token = self.config.get("user", "tokens//bearer//access_token")
        response = self.session.post(
            constants.AMAZON_GAMING_GRAPHQL,
            data=data,
            headers={"x-amz-access-token": token},
        )
        if not response.ok:
            return None

        return response.json()

    def get_offers(self):
        return self.make_graphql_request(
            '{"query":"query{primeOffers(dateOverride:null,group:null){catalogId,title,startTime,endTime,deliveryMethod,tags{type,tag},productList{sku,vendor},content{publisher},assets{location2x},offerAssets{screenshots{location}},self{eligibility{canClaim,isClaimed,isPrimeGaming,maxOrdersExceeded,inRestrictedMarketplace,missingRequiredAccountLink,conflictingClaimAccount{obfuscatedEmail}}},game{id,gameplayVideoLinks,keywords,releaseDate,esrb,pegi,usk,website,genres,gameModes,externalWebsites{socialMediaType,link},developerName,logoImage{defaultMedia{src1x,src2x,type},tablet{src1x,src2x,type},desktop{src1x,src2x,type},description,alt,videoPlaceholderImage{src1x,src2x,type}},pgCrownImage{defaultMedia{src1x,src2x,type},tablet{src1x,src2x,type},desktop{src1x,src2x,type},description,alt,videoPlaceholderImage{src1x,src2x,type}},trailerImage{defaultMedia{src1x,src2x,type},tablet{src1x,src2x,type},desktop{src1x,src2x,type},description,alt,videoPlaceholderImage{src1x,src2x,type}},publisher,background{defaultMedia{src1x,src2x,type},tablet{src1x,src2x,type},desktop{src1x,src2x,type},description,alt,videoPlaceholderImage{src1x,src2x,type}},banner{defaultMedia{src1x,src2x,type},tablet{src1x,src2x,type},desktop{src1x,src2x,type},description,alt,videoPlaceholderImage{src1x,src2x,type}},description,otherDevelopers}}}"}'
        )
