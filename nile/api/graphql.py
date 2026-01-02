import requests
import locale
import nile.constants as constants
from nile.utils.config import ConfigType
import hashlib


class GraphQLHandler:
    def __init__(self, config_manager):
        self.config = config_manager
        self.session = requests.Session()
        # This will cause problems on certain systems for sure
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
        uid = self.config.get('current_user', 'user_id').encode('utf-8')
        store_name = hashlib.md5(uid).hexdigest()
        enc_key = hashlib.sha256(uid).digest()
        token = self.config.get(store_name, "tokens//bearer//access_token", cfg_type=ConfigType.JSONENC, enc_key=enc_key)

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

    def get_account_entitlement(self):
        return self.make_graphql_request(
            '{"query": "query{currentUser{isTwitchPrime,isAmazonPrime,twitchAccounts{tuid}}}"}'
        )
